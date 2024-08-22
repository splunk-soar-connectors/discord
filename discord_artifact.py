from dataclasses import dataclass, field


@dataclass
class Cef:
    URL: str = ""
    Type: str = ""
    Description: str = ""


@dataclass
class Artifact:
    container_id: str
    name: str
    cef: dict = field(default_factory=dict)
