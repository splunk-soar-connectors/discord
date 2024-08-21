import dataclasses
from dataclasses import dataclass, field


@dataclass
class Artifact:
    container_id: str
    name: str
    cef: dict = field(default_factory=lambda: {"URL": "", "Type": "", "Description": ""})


def artifact_to_dict(artifact: Artifact):
    return dataclasses.asdict(artifact)