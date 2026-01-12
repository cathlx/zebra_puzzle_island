import json
import matplotlib.pyplot as plt 
import numpy as np 
import pandas as pd 
import random
import seaborn as sns
import yaml 

from typing import Any

from configs.config_manager import Config 
from scripts.setting import * 

def save_to_yaml(data: dict[str, Any], output_path: str = 'sample.yaml'):
    """Generate a sample YAML configuration for testing"""
    with open(output_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

class ExperimentManager:
    def __init__(self, config_path: str) -> None:
        self.cfg = Config.from_yaml(config_path)
        self.output_dir = self.cfg.get_output_directory()
        
    def set_seed(self) -> None:
        random.seed(self.cfg.simulation.random_seed)
        np.random.seed(self.cfg.simulation.random_seed)

    def to_dict(self) -> dict[str, Any]:
        return {
            'experiment_name': self.cfg.experiment_name, 
            'experiment_id': self.cfg.experiment_id,
            'num_days': self.cfg.simulation.num_days,
            'tracked_metrics': self.cfg.metrics.tracked
        }

    def _collect_daily_metrics(self, island: Island, day: int) -> dict[str, Any]:
        all_metrics = {
            'total_awareness': len(island.facts),
            # 'average_agent_awareness': np.mean([len(a.known_facts) for a in island.agents]),
            # 'std_agent_awareness': np.std([len(a.known_facts) for a in island.agents]),
            # 'meetings_today': island.meetings_today,
            # 'unique_roads_traveled': np.sum(island.road_usage > 0),
            # 'max_pheromone': np.max(island.pheromones) if hasattr(island, 'pheromones') else 0
        } | {f'agent{i + 1}_awareness': len(agent.known_facts) for i, agent in enumerate(island.agents)}

        return pd.Series(all_metrics)[self.cfg.metrics.tracked].to_dict()
    
    def run_experiment(self, yaml_representation: bool = True, save_results: bool = True, save_island_csv: bool = False) -> dict[str, Any]:
        self.set_seed()

        island = get_island_from_cfg(self.cfg, save_island_csv)

        metrics = dict()

        if yaml_representation:
            experiment_repr = self.to_dict() | island.to_dict()
            save_to_yaml(experiment_repr, self.output_dir / 'setting.yaml')

        for day in range(self.cfg.simulation.num_days):
            island.day()
            if day % self.cfg.output.save_interval == 0 or day == self.cfg.simulation.num_days - 1:
                metrics[day] = self._collect_daily_metrics(island, day)

        if save_results:
            self._save_results(island, metrics)

        return self.output_dir 

    def _save_results(self, island: Island, metrics: dict[str, Any]) -> None:
        metrics_df = pd.DataFrame.from_dict(metrics)
        metrics_df.to_csv(self.output_dir / 'metrics.csv', index=True)

        # with open(self.output_dir / 'metrics.json', 'w') as file:
        #     json.dump(metrics, file, indent=2)
        
        if self.cfg.output.save_final_state:
            facts_dir = self.output_dir / 'facts'
            facts_dir.mkdir(exist_ok=True)
            island.log_knowledge(facts_dir)

    def plot_results(self, figsize: tuple[int, int] = (10, 6)) -> None:
        metrics_df = pd.read_csv(self.output_dir / 'metrics.csv', index_col=0).T

        plt.figure(figsize=figsize)

        sns.lineplot(metrics_df)
        plt.legend()

        plt.title('Metrics')
        plt.xlabel('Day')
        plt.xlim(0)

        plt.tight_layout()
        plt.show()
