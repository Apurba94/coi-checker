import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from coi_checker.cli import main
from coi_checker.core import check_reviewers, coauthor_index, load_papers, name_key

BIB = """@article{a,
  author = {Silva, Ana and Chen, Bo and Novak, Petra},
  year = {2024},
}
@article{b,
  author = {Ana M. Silva and Jan van der Berg},
  year = {2015},
}
@article{c,
  author = {Novak, P. and M{\\"u}ller, Kai},
  year = {2023},
}
"""
REVIEWERS = [{"name": "Petra Novak", "affiliation": "Charles University"},
             {"name": "J. van der Berg", "affiliation": "Utrecht University"},
             {"name": "Kai Mueller", "affiliation": "ETH Zurich"},
             {"name": "Kai Müller", "affiliation": "ETH Zurich"},
             {"name": "Lena Ito", "affiliation": "University of Tokyo"},
             {"name": "Ravi Rao", "affiliation": "Department of Biology, University of Lisbon"}]


def papers():
    d = tempfile.mkdtemp()
    p = os.path.join(d, "pubs.bib")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(BIB)
    return p


class NameTests(unittest.TestCase):
    def test_name_key(self):
        self.assertEqual(name_key("Silva, Ana M."), "silva|a")
        self.assertEqual(name_key("Ana M. Silva"), "silva|a")
        self.assertEqual(name_key("Jan van der Berg"), "vanderberg|j")
        self.assertEqual(name_key("M{\\\"u}ller, Kai"), "muller|k")

    def test_load_and_index(self):
        ps = load_papers(papers())
        self.assertEqual([y for y, _ in ps], [2024, 2015, 2023])
        idx = coauthor_index(ps)
        self.assertEqual(idx["silva|a"]["novak|p"], [2024])


class CheckTests(unittest.TestCase):
    def test_conflicts(self):
        res = {r["reviewer"]: r for r in check_reviewers(["Ana Silva", "Bo Chen"], REVIEWERS, load_papers(papers()),
                                                          window=5, current_year=2026,
                                                          author_affils=["University of Lisbon"])}
        self.assertEqual(res["Petra Novak"]["severity"], "high")
        self.assertIn("co-authored with Ana Silva in 2024", res["Petra Novak"]["conflicts"][0])
        self.assertEqual(res["J. van der Berg"]["severity"], "medium")          # 2015 is outside the window
        self.assertEqual(res["Kai Müller"]["severity"], "medium")               # shares co-author Novak
        self.assertEqual(res["Kai Mueller"]["severity"], "none")                # different spelling, not matched
        self.assertEqual(res["Ravi Rao"]["severity"], "high")                   # same institution
        self.assertEqual(res["Lena Ito"]["conflicts"], [])

    def test_author_as_reviewer_and_cli(self):
        res = check_reviewers(["Ana Silva"], [{"name": "A. Silva", "affiliation": ""}], [])
        self.assertEqual(res[0]["severity"], "high")
        with tempfile.TemporaryDirectory() as d:
            rp = os.path.join(d, "rev.csv")
            with open(rp, "w", encoding="utf-8") as fh:
                fh.write("name,affiliation\nLena Ito,University of Tokyo\n")
            with redirect_stdout(io.StringIO()) as buf:
                self.assertEqual(main(["--authors", "Ana Silva; Bo Chen", "--reviewers", rp, "--papers", papers()]), 0)
            self.assertIn("NONE    Lena Ito", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
