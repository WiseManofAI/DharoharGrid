// Local stand-in for the Supabase tables described in Phase 2, so the graph
// is inspectable before real credentials are wired up. Shape mirrors what
// useDharoharData expects back from Supabase:
//   nodes:  { id, title, content }
//   edges:  { id, source, target, status: "confirmed" | "ai_discovered" }

export const mockNodes = [
  { id: "hawa-mahal", title: "Hawa Mahal", content: "# Hawa Mahal\n\nThe 'Palace of Winds' in Jaipur, built in 1799 from red and pink sandstone, with 953 small windows (*jharokhas*) designed to let royal women observe street life unseen.\n\n**Type:** Tangible — Architecture\n**Region:** Jaipur, Rajasthan" },
  { id: "jaipur-city", title: "Jaipur (Pink City)", content: "# Jaipur\n\nFounded in 1727 by Sawai Jai Singh II, planned on Vastu Shastra principles — one of India's earliest examples of grid-based urban design.\n\n**Type:** Tangible — Urban Heritage" },
  { id: "block-printing", title: "Bagru Hand Block Printing", content: "# Bagru Hand Block Printing\n\nA natural-dye block printing tradition from Bagru village near Jaipur, using hand-carved teak blocks and indigo/madder-root dyes.\n\n**Type:** Living Craft" },
  { id: "kathputli", title: "Kathputli Puppetry", content: "# Kathputli\n\nRajasthani string-puppet theatre performed by the Bhat community, traditionally narrating tales of Rajput valor and folklore.\n\n**Type:** Intangible — Performing Art" },
  { id: "phad-painting", title: "Phad Painting", content: "# Phad Painting\n\nScroll paintings on cloth depicting the epics of local deities like Pabuji and Devnarayan, traditionally sung aloud by Bhopa priest-singers as the scroll unrolls.\n\n**Type:** Living Craft — Scroll Art" },
  { id: "amber-fort", title: "Amber Fort", content: "# Amber Fort\n\nHilltop fort-palace overlooking Maota Lake, built by Raja Man Singh I in 1592, blending Rajput and Mughal architectural styles.\n\n**Type:** Tangible — Architecture" },
  { id: "jaipur-gharana", title: "Jaipur-Atrauli Gharana", content: "# Jaipur-Atrauli Gharana\n\nA khyal singing tradition founded by Ustad Alladiya Khan, known for its intricate, angular melodic movement (*layakari*).\n\n**Type:** Intangible — Music Lineage" },
  { id: "sanganeri-print", title: "Sanganeri Printing", content: "# Sanganeri Printing\n\nA finer, floral-motif block print style from Sanganer, distinguished from Bagru by its white background and delicate botanical patterns.\n\n**Type:** Living Craft" },
];

export const mockEdges = [
  { id: "e1", source: "hawa-mahal", target: "jaipur-city", status: "confirmed" },
  { id: "e2", source: "amber-fort", target: "jaipur-city", status: "confirmed" },
  { id: "e3", source: "block-printing", target: "sanganeri-print", status: "confirmed" },
  { id: "e4", source: "kathputli", target: "phad-painting", status: "ai_discovered" },
  { id: "e5", source: "phad-painting", target: "jaipur-gharana", status: "ai_discovered" },
  { id: "e6", source: "jaipur-city", target: "block-printing", status: "confirmed" },
  { id: "e7", source: "jaipur-city", target: "jaipur-gharana", status: "ai_discovered" },
  { id: "e8", source: "hawa-mahal", target: "amber-fort", status: "ai_discovered" },
];
