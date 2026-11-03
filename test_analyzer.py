import json
import unittest
from text_analyzer import summarize_text, extract_keywords

class TestTextAnalyzer(unittest.TestCase):
    def test_summary_default(self):
        txt = "Artificial intelligence is transforming education. Machine learning helps educational systems analyze student data. AI can support personalized learning."
        summary = summarize_text(txt)
        self.assertTrue(isinstance(summary, str))
        self.assertGreaterEqual(len(summary.split()), 1)

    def test_summary_adjustable(self):
        txt = "First sentence. Second sentence! Third sentence? Fourth sentence."
        summary = summarize_text(txt, sentence_count=2)
        self.assertLessEqual(len(summary.split('.')), 3)  # 2 sentences => at most 3 periods

    def test_keywords(self):
        txt = "Python Python data analysis data science science"
        kw = extract_keywords(txt, top_n=2)
        self.assertEqual(len(kw), 2)
        self.assertEqual(kw[0]["keyword"], "python")
        self.assertEqual(kw[0]["count"], 2)

    def test_empty_input(self):
        self.assertEqual(summarize_text(""), "")
        self.assertEqual(extract_keywords(""), [])

    def test_short_text(self):
        txt = "Hello world"
        self.assertEqual(summarize_text(txt), txt)
        kw = extract_keywords(txt)
        # may return empty if stopwords filter removes everything
        self.assertIsInstance(kw, list)

if __name__ == "__main__":
    unittest.main()
