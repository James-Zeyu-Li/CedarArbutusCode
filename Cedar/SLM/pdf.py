from pypdf import PdfReader
from kg_gen import KGGen, Graph


def get_pdf_pages_text(path):
	reader = PdfReader(path)
	return [page.extract_text() for page in reader.pages]


# Makes windows for chunk ingestion
def make_pdf_chunks(pages_text, expand_chars=50):
	chunks = []
	for i, page_text in enumerate(pages_text):
		chunk = page_text
		if (i-1) >= 0:
			chunk = pages_text[i-1][max(len(pages_text[i-1])-expand_chars, 0):] + chunk
		if (i+1) < len(pages_text):
			chunk = chunk + pages_text[i+1][:expand_chars]
		chunks.append(chunk)
	return chunks


# Creates collections of words, returns them and the page range they were pulled from
def make_chunks(pages, chunk_size=100, spillover=10):
	# The number of words passed at the end of a page
	page_position = {}
	cur_count = 0
	for i, page_text in enumerate(pages):
		words = page_text.split()
		cur_count += len(words)
		page_position[i+1] = cur_count

	# Reverse to find page number by position
	position_page = [(v, k) for k, v in page_position.items()]
	position_page.sort()

	# Collect (chunk, (st, en))
	chunks_sources = []
	words = [word for page in pages for word in page.split()]
	i = 0
	while True:
		segment = words[i:(i+chunk_size)]
		
		st = 0
		en = len(pages)
		for position, page in position_page:
			if position > i:
				if position > i + chunk_size:
					en = page
					break
			else:
				st = page

		# Splitting by words does lose whitespace information
		# Impact unknown 
		chunks_sources.append((" ".join(segment), (st, en)))

		i += len(segment)
		if i < len(words):
			i -= spillover
		else:
			break

	return chunks_sources


if __name__ == "__main__":
	pages = get_pdf_pages_text("fema_nims_doctrine-2017.pdf")
	for i, (entry, (st, en)) in enumerate(make_chunks(pages)[:2]):
		print(i, st, en)
	# for g in make_chunks(pages)[:2]:
		# print(g)