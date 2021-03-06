# File: t (Python 2.4)

from toontown.toonbase.ToontownGlobals import *
import RegenTreasurePlannerAI
import DistributedDDTreasureAI

class DDTreasurePlannerAI(RegenTreasurePlannerAI.RegenTreasurePlannerAI):
    
    def __init__(self, zoneId):
        self.healAmount = 10
        RegenTreasurePlannerAI.RegenTreasurePlannerAI.__init__(self, zoneId, DistributedDDTreasureAI.DistributedDDTreasureAI, 'DDTreasurePlanner', 20, 2)

    
    def initSpawnPoints(self):
        self.spawnPoints = [
            (52.907200000000003, -23.476800000000001, -12.308),
            (35.3827, -51.919600000000003, -12.308),
            (17.4252, -57.310699999999997, -12.308),
            (-0.71605399999999997, -68.5, -12.308),
            (-29.0169, -66.8887, -12.308),
            (-63.491999999999997, -64.219099999999997, -12.308),
            (-72.2423, -58.368600000000001, -12.308),
            (-97.9602, -42.890500000000003, -12.308),
            (-102.215, -34.151899999999998, -12.308),
            (-102.97799999999999, -4.0906500000000001, -12.308),
            (-101.30500000000001, 30.645399999999999, -12.308),
            (-45.062100000000001, -21.008800000000001, -12.308),
            (-11.404299999999999, -29.081600000000002, -12.308),
            (2.33548, -7.7172200000000002, -12.308),
            (-8.6430000000000007, 33.989100000000001, -12.308),
            (-53.223999999999997, 18.129300000000001, -12.308),
            (-99.722499999999997, -8.1297999999999995, -12.308),
            (-100.45699999999999, 28.350999999999999, -12.308),
            (-76.794600000000003, 4.2119900000000001, -12.308),
            (-64.913700000000006, 37.576500000000003, -12.308),
            (-17.607500000000002, 102.13500000000001, -12.308),
            (-23.411200000000001, 127.777, -12.308),
            (-11.3513, 128.99100000000001, -12.308),
            (-14.1068, 83.204300000000003, -12.308),
            (53.268500000000003, 24.358499999999999, -12.308),
            (41.419699999999999, 4.3538399999999999, -12.308)]
        return self.spawnPoints


