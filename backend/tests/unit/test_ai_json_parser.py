import unittest

from fastapi import HTTPException


class AiJsonParserTest(unittest.TestCase):
    def test_ai_json_parser_accepts_fenced_json(self) -> None:
        from app.utils.ai_json import parse_ai_json_object

        parsed = parse_ai_json_object(
            '```json\n{"category": "餐饮", "reason": "备注包含午餐"}\n```'
        )

        self.assertEqual(parsed["category"], "餐饮")
        self.assertEqual(parsed["reason"], "备注包含午餐")

    def test_ai_json_parser_rejects_non_json(self) -> None:
        from app.utils.ai_json import parse_ai_json_object

        with self.assertRaises(HTTPException):
            parse_ai_json_object("无法分类")


if __name__ == "__main__":
    unittest.main()
