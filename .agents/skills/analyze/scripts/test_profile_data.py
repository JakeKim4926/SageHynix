"""Self-tests for profile_data.py. 기대값은 아래 작은 파일을 손으로 센 값이다.

Run: python3 -m unittest discover -s .agents/skills/analyze/scripts -p "test_*.py"
"""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from profile_data import profile  # noqa: E402


class Profile(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)

    def write(self, name, text, encoding="utf-8"):
        p = self.dir / name
        p.write_text(text, encoding=encoding)
        return p

    def test_csv_counts_missing_duplicates_ranges(self):
        p = self.write("lots.csv", "id,line,good,total,ts\n"
                                   "1,A,95,100,2024-01-01\n"
                                   "2,A,,0,2024-01-02\n"
                                   "3,B,80,100,2024-01-03\n"
                                   "3,B,80,100,2024-01-03\n")
        out = profile(p)
        self.assertIn("행 4 · 열 5 · 중복 행 1", out)
        self.assertIn("| good | 정수 | 25.0% | 2 | 80 ~ 95 · 값 분포: 80 2, 95 1 |", out)
        self.assertIn("| total | 정수 | 0.0% | 2 | 0 ~ 100 · 값 분포: 100 3, 0 1 |", out)
        self.assertIn("| ts | 날짜 | 0.0% | 3 | 2024-01-01 ~ 2024-01-03 · 값 분포: 2024-01-03 2, 2024-01-01 1, 2024-01-02 1 |", out)
        self.assertIn("| line | 문자열 | 0.0% | 2 | 값 분포: A 2, B 2 |", out)
        self.assertNotIn("키 후보", out)  # id 3이 두 번

    def test_cp949_csv_and_key_candidate(self):
        p = self.write("eqp.csv", "설비,값\nE1,1.5\nE2,2\n", encoding="cp949")
        out = profile(p)
        self.assertIn("인코딩 cp949", out)
        self.assertIn("| 설비 | 문자열 | 0.0% | 2 | 키 후보 |", out)
        self.assertIn("| 값 | 실수 | 0.0% | 2 | 1.5 ~ 2 |", out)

    def test_jsonl_and_ragged_csv(self):
        out = profile(self.write("a.jsonl", '{"k":"x","v":1}\n{"k":"y"}\n'))
        self.assertIn("행 2 · 열 2", out)
        self.assertIn("| v | 정수 | 50.0% | 1 | 1 ~ 1 |", out)
        out = profile(self.write("b.csv", "a,b\n1,2\n3\n"))
        self.assertIn("열 수가 헤더와 다른 행 1", out)

    def test_unsupported_format_is_reported_not_guessed(self):
        out = profile(self.write("c.xlsx", ""))
        self.assertIn("읽지 않음", out)


if __name__ == "__main__":
    unittest.main()
