import unittest

from app.models import MotorcycleModel, RecommendationRequest
from app.price_models import MotorcyclePriceBand
from app.seed import MOTORCYCLES, PRICE_BANDS
from app.services.recommender import recommend


def _models():
    return [MotorcycleModel(**item) for item in MOTORCYCLES]


def _price_bands():
    return [
        MotorcyclePriceBand(
            model_id=model_id,
            model_name=model_name,
            year=year,
            condition_type=condition_type,
            price_min=price_min,
            price_max=price_max,
            note=note,
        )
        for model_id, model_name, year, condition_type, price_min, price_max, note in PRICE_BANDS
    ]


def _request(**overrides):
    data = {
        "budget": 300,
        "experience_level": "none",
        "delivery_plan": "try",
        "daily_hours": 3,
        "used_ok": False,
        "priority": "cost",
        "area_type": "flat",
        "body_preference": "none",
        "model_preference": "none",
    }
    data.update(overrides)
    return RecommendationRequest(**data)


def _scores(**overrides):
    return recommend(_request(**overrides), _models(), _price_bands())


class RecommenderTest(unittest.TestCase):
    def test_low_budget_without_used_keeps_unaffordable_models_down(self):
        scores = _scores(
            budget=300,
            delivery_plan="long_term",
            daily_hours=8,
            priority="long_term",
            used_ok=False,
        )
        by_id = {score.model_id: score for score in scores}

        self.assertEqual(scores[0].model_id, "vf100r")
        self.assertLess(by_id["pcx"].score_detail["availability_penalty"], 0)
        self.assertEqual(by_id["pcx"].price_guidance.bands, [])

    def test_low_budget_try_cost_picks_vf100r(self):
        scores = _scores(budget=300, delivery_plan="try", priority="cost", used_ok=False)

        self.assertEqual(scores[0].model_id, "vf100r")

    def test_long_term_with_enough_budget_picks_pcx(self):
        scores = _scores(
            budget=550,
            experience_level="some",
            delivery_plan="long_term",
            daily_hours=6,
            priority="popularity",
            model_preference="popular",
            used_ok=False,
        )

        self.assertEqual(scores[0].model_id, "pcx")

    def test_pcx_alternative_preference_picks_nmax(self):
        scores = _scores(
            budget=550,
            experience_level="some",
            delivery_plan="long_term",
            daily_hours=6,
            priority="popularity",
            model_preference="pcx_alternative",
            used_ok=False,
        )

        self.assertEqual(scores[0].model_id, "nmax")

    def test_experience_level_changes_model_score(self):
        none = {score.model_id: score for score in _scores(experience_level="none")}
        experienced = {score.model_id: score for score in _scores(experience_level="experienced")}

        self.assertGreater(
            none["vf100r"].score_detail["experience_bonus"],
            experienced["vf100r"].score_detail["experience_bonus"],
        )


if __name__ == "__main__":
    unittest.main()
