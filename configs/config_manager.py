import datetime
import yaml

from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Any, Self, Optional


@dataclass
class InputConfig:
    people_states: Optional[str] = None
    action_probs: Optional[str] = None
    distance_matrix: Optional[str] = None

@dataclass
class SimulationConfig:
    num_agents: int = 6
    num_days: int = 100
    random_seed: Optional[int] = 42
    verbose: bool = False

@dataclass
class StrategiesConfig:
    mandatory_return: bool = False
    visit_strategies: dict[int, str] = field(default_factory=lambda: {i + 1: 'random' for i in range(6)})

@dataclass
class ACOConfig:
    pheromone_deposit: list[float] = field(default_factory=lambda: [1.0] * 6)
    exp_time_decay: float = 7.0

@dataclass
class OutputConfig:
    directory: str = 'output'
    save_interval: int = 10
    save_final_state: bool = True

@dataclass
class MetricsConfig:
    tracked: list[str] = field(default_factory=lambda: [
        'agent_awareness',
        'meetings_per_day'
    ])

@dataclass
class Config:
    experiment_name: str = 'default_experiment'
    experiment_id: str = field(default_factory=lambda: datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    description: str = 'None'
    
    input: InputConfig = field(default_factory=InputConfig)
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    strategies: StrategiesConfig = field(default_factory=StrategiesConfig)
    aco: ACOConfig = field(default_factory=ACOConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> Self:
        """Load config from nested YAML file"""
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        return cls(
            experiment_name=data.get('experiment_name', 'default_experiment'),
            description=data.get('description', 'None'),
            input=InputConfig(**data.get('input', {})),
            simulation=SimulationConfig(**data.get('simulation', {})),
            strategies=StrategiesConfig(**data.get('strategies', {})),
            aco=ACOConfig(**data.get('aco', {})),
            output=OutputConfig(**data.get('output', {})),
            metrics=MetricsConfig(**data.get('metrics', {}))
        )
    
    def to_yaml(self, output_path: str) -> None:
        """Save config to YAML file"""

        config_dict = {
            'experiment_name': self.experiment_name,
            'experiment_id': self.experiment_id,
            'input': asdict(self.input),
            'simulation': asdict(self.simulation),
            'strategies': asdict(self.strategies),
            'aco': asdict(self.aco),
            'output': asdict(self.output),
            'metrics': asdict(self.metrics)
        }
        
        with open(output_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            'experiment_name': self.experiment_name,
            'experiment_id': self.experiment_id,
            'input': asdict(self.input),
            'simulation': asdict(self.simulation),
            'strategies': asdict(self.strategies),
            'aco': asdict(self.aco),
            'output': asdict(self.output),
            'metrics': asdict(self.metrics)
        }
    
    def get_output_directory(self) -> Path:
        """Get unique output directory for this experiment"""
        dir_name = f"{self.experiment_name}_{self.experiment_id}"
        output_path = Path(self.output.directory) / dir_name
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path
