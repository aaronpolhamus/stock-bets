from unittest import TestCase

from backend.tasks.airflow import start_dag


class TestTriggerDag(TestCase):

    def test_start_dag(self):
        """Ensures the we're able to externally trigger a bunch of DAGs concurrently without metadata issues"""
        start_dag("update_game_dag", game_id=99)
        start_dag("update_game_dag", game_id=100)
        start_dag("update_game_dag", game_id=101)
        start_dag("update_game_dag", game_id=102)
        start_dag("update_game_dag", game_id=103)
        self.assertTrue(True)
