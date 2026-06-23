import unittest

from app.services.faq_search import answer_faq


class FaqSearchTest(unittest.TestCase):
    def test_matches_insurance_question(self):
        response = answer_faq("배달 보험은 뭘 확인해야 하나요?")

        self.assertEqual(response.matched_title, "보험")
        self.assertGreater(response.confidence, 0)

    def test_matches_nmax_question(self):
        response = answer_faq("NMAX가 PCX 대안으로 어떤 장점이 있어?")

        self.assertEqual(response.matched_title, "NMAX")

    def test_unknown_question_returns_fallback(self):
        response = answer_faq("오늘 점심 메뉴 추천")

        self.assertIsNone(response.matched_title)
        self.assertEqual(response.confidence, 0)


if __name__ == "__main__":
    unittest.main()
