from dataclasses import dataclass

# simple object to store ingredients of the abo boxes
@dataclass
class Ingredient:
    name: str
    recipes_url: str = None
