from project_paths import ROOT as PROJECT_ROOT, source_path
import re


def clause_chunks(documents, max_chars=700):
    """Pack sentence units within paragraphs; preserve every original character."""
    if max_chars < 32:
        raise ValueError('max_chars must be at least 32.')
    chunks = []
    for file_path, text in sorted(documents.items()):
        paragraph_ends = [m.end() for m in re.finditer(r'\n\s*\n|\n(?=\s*(?:\d+(?:\.\d+)*[.)]?|SECTION\s+\d+)\s)', text)]
        start = 0
        for end in sorted(set(paragraph_ends+[len(text)])):
            if end <= start:
                continue
            boundaries = [start+m.end() for m in re.finditer(r'(?<=[.;!?])\s+(?=[A-Z(])',text[start:end])]+[end]
            cursor = start
            packed_start = start
            for boundary in boundaries:
                if boundary-packed_start > max_chars and cursor > packed_start:
                    chunks.append(dict(file_path=file_path,start=packed_start,end=cursor,text=text[packed_start:cursor]))
                    packed_start = cursor
                while boundary-packed_start > max_chars:
                    limit = packed_start+max_chars
                    split = text.rfind(' ',packed_start,limit)
                    split = split+1 if split > packed_start else limit
                    chunks.append(dict(file_path=file_path,start=packed_start,end=split,text=text[packed_start:split]))
                    packed_start = split
                cursor = boundary
            if packed_start < end:
                chunks.append(dict(file_path=file_path,start=packed_start,end=end,text=text[packed_start:end]))
            start = end
    return chunks


class AbstentionRetriever:
    def __init__(self, base, threshold):
        self.base = base
        self.threshold = threshold
        self.config = dict(base.config, abstention_threshold=threshold)

    def search(self, query, k=5):
        hits = self.base.search(query,k)
        return hits if hits and hits[0]['score'] > self.threshold else []
