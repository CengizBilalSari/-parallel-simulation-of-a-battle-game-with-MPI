"""
The unit class is parent class of the Earth,Water,Fire and Air classes.
Its attributes are unit type, health, attack power, healing rate and attack pattern
"""
class Unit:
    def __init__(self, unit_type="neutral",full_health=0,health=0,attack_power=0,healing_rate=0,attack_pattern=[],attack=False):
        self.unit_type = unit_type
        self.health=health
        self.full_health= full_health
        self.attack_power=attack_power
        self.healing_rate=healing_rate
        self.attack_pattern=attack_pattern
        self.attack= attack
    

    def __str__(self):
        return f"{self.unit_type} ({self.health} HP, {self.attack_power} AP)"


"""
In these 4 classes the specific attributes are assigned to classes and the str method is overwritten from the Unit class.


"""
class Earth(Unit):
    def __init__(self):
        super().__init__(unit_type="Earth", full_health=18,health=18, attack_power=2, healing_rate=3,
                         attack_pattern=[(0, -1), (0, 1), (-1, 0), (1, 0)],attack=False)
    def __str__(self):
        return f"Earth Unit ({self.health} HP, {self.attack_power} AP, {self.healing_rate} Healing Rate)"

class Fire(Unit):
    def __init__(self):
        super().__init__(unit_type="Fire", full_health=12,health=12, attack_power=4, healing_rate=1,
                         attack_pattern=[(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)],attack=False)
        self.inferno = False
    def __str__(self):
        return f"Fire Unit ({self.health} HP, {self.attack_power} AP, {self.healing_rate} Healing Rate)"
    
    def apply_inferno(self):
        if(self.attack_power<6):
            self.attack_power+=1

class Water(Unit):
    def __init__(self):
        super().__init__(unit_type="Water",full_health=14,health=14,attack_power=3,healing_rate=2,attack_pattern=[(-1,-1),(-1,1),(1,-1),(1,1)],attack=False)
    def __str__(self):
        return f"Water Unit ({self.health} HP, {self.attack_power} AP, {self.healing_rate} Healing Rate)"
    

class Air(Unit):
   def __init__(self, attack_power=2, health=10):
        super().__init__(unit_type="Air", full_health=10, health=health, attack_power=attack_power, healing_rate=2,
                         attack_pattern=[(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)], attack=False)
   def __str__(self):
        return f"Air Unit ({self.health} HP, {self.attack_power} AP, {self.healing_rate} Healing Rate)"

