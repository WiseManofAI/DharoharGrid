from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .. import config
from ..clients import get_embedder, get_groq, get_supabase

router = APIRouter(prefix="/api/v1/docent", tags=["docent"])


class AskRequest(BaseModel):
    user_query: str


class AskResponse(BaseModel):
    answer: str
    refused: bool


SYSTEM_PROMPT = (
    "You are a knowledgeable museum docent. "
    "Answer the user's question using ONLY the verified information "
    "provided in the context below. "
    "Do not add outside knowledge or speculate beyond what is given. "
    "If the context does not fully answer the question, say so honestly."
)


@router.post("/ask", response_model=AskResponse)
def ask_docent(request: AskRequest):
    user_query = request.user_query.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="user_query cannot be empty.")

    embedding_model = get_embedder()
    supabase = get_supabase()

    query_embedding = embedding_model.encode(user_query).tolist()

    try:
        rpc_response = supabase.rpc(
            "match_cultural_nodes",
            {"query_embedding": query_embedding, "match_count": config.MATCH_COUNT},
        ).execute()
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Supabase search failed: {e}")

    matches = rpc_response.data or []
    if not matches:
        return AskResponse(answer="I don't have verified information on that specific aspect.", refused=True)

    top_score = matches[0]["similarity"]
    if top_score < config.SIMILARITY_THRESHOLD:
        return AskResponse(answer="I don't have verified information on that specific aspect.", refused=True)

    context_chunks = [f"Title: {m['title']}\nContent: {m['content']}" for m in matches]
    combined_context = "\n\n---\n\n".join(context_chunks)

    user_prompt = (
        f"Context:\n{combined_context}\n\n"
        f"Question: {user_query}\n\n"
        "Answer the question using only the context above."
    )

    groq_client = get_groq()
    try:
        chat_completion = groq_client.chat.completions.create(
            model=config.GROQ_MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
        final_answer = chat_completion.choices[0].message.content
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Groq API call failed: {e}")

    return AskResponse(answer=final_answer, refused=False)
