def clean_pdf_text(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # join hyphenated line breaks: "responsi-\nbility" -> "responsibility"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    # join broken lines inside same paragraph
    text = re.sub(r"(?<![.!?:])\n(?!\n)", " ", text)
    # normalize paragraph breaks
    text = re.sub(r"\n{3,}", "\n\n", text)
    # collapse repeated spaces/tabs
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()
# document_clean = clean_pdf_text(document)

# Rudimentary: Define context that we will pass through a system_message - 
# very rudimentary entry version of a RAG - dynamic context injection 
Topic_Context = {
    frozenset(["books"]): "genre: realistic fiction, one of Mamta's favourite books was the Day of the Jackal by Fredrick Forsythe.",
    frozenset(["icecream","food","cold"]): "Mamta's favourite icecream flavour is coffee.",
    frozenset(["netflix","movies","tv","shows"]): "action, espionage, political thrillers, medical dramas, kdrama, vegetarian cooking shows",
    frozenset(["cooking"]): "Mamta enjoys watching cooking shows but does not like cooking. It's a chicken and egg problem. The food doesn't turn out good and so she doesn't enjoy cooking and so the food doesn't turn out", 
    frozenset(["pizza","food","hot","pineapple"]): "Mamta doesn't mind pineapple on pizza but her favourite toppings are onions and jalapenos.",
    frozenset(["fitness","health"]): "Mamta has run a half marathon, she enjoys yoga, biking, hiking and kayaking",
    frozenset(["hobbies"]): "Mamta loves doing jigsaw puzzles",
}  