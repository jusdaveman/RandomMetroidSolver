# check if a stats db is available
try:
    # python3.7 -m pip install pip
    # pip3.7 install mysql-connector-python --user
    import mysql.connector
    from db_params import dbParams
    dbAvailable = True
except:
    dbAvailable = False

from parameters import medium, hard, harder, hardcore, mania
from utils import removeChars

class DB:
    def __init__(self):
        self.dbAvailable = dbAvailable
        if self.dbAvailable == False:
            return

        try:
            self.conn = mysql.connector.connect(**dbParams)
            self.cursor = self.conn.cursor()
        except Exception as e:
            print("DB.__init__::error connect/create cursor: {}".format(e))
            self.dbAvailable = False

    def close(self):
        if self.dbAvailable == False:
            return

        try:
            self.conn.commit()
            self.cursor.close()
            self.conn.close()
        except Exception as e:
            print("DB.close::error: {}".format(e))

    def commit(self):
        if self.dbAvailable == False:
            return

        try:
            self.conn.commit()
        except Exception as e:
            print("DB.commit::error: {}".format(e))

    # write data
    def initSolver(self):
        if self.dbAvailable == False:
            return None

        try:
            sql = "insert into solver (action_time) values (now());"
            self.cursor.execute(sql)
            return self.cursor.lastrowid
        except Exception as e:
            print("DB.initSolver::error execute: {} error: {}".format(sql, e))
            self.dbAvailable = False

    def addSolverParams(self, id, romFileName, preset, difficultyTarget, pickupStrategy, itemsForbidden):
        if self.dbAvailable == False or id == None:
            return

        try:
            sql = "insert into solver_params values (%d, '%s', '%s', %d, '%s');" % (id, romFileName, preset, difficultyTarget, pickupStrategy)
            self.cursor.execute(sql)

            sql = "insert into solver_items_forbidden values (%d, '%s');"
            for item in itemsForbidden:
                self.cursor.execute(sql % (id, item))
        except Exception as e:
            print("DB.addSolverParams::error execute: {}".format(e))
            self.dbAvailable = False

    def addSolverResult(self, id, returnCode, duration, result):
        if self.dbAvailable == False:
            return

        def lenNone(var):
            if var == None:
                return 0
            else:
                return len(var)

        try:
            if returnCode == 0:
                sql = "insert into solver_collected_items values (%d, '%s', %d);"
                for item, count in result['collectedItems'].items():
                    if count > 0:
                        self.cursor.execute(sql % (id, item, count))

                sql = "insert into solver_result values (%d, %d, %f, %d, %d, %d, %s, %d, %d, %d, %d, %d);" % (id, returnCode, duration, result['difficulty'], result['knowsUsed'][0], result['knowsUsed'][1], result['itemsOk'], lenNone(result['remainTry']), lenNone(result['remainMajors']), lenNone(result['remainMinors']), lenNone(result['skippedMajors']), lenNone(result['unavailMajors']))
            else:
                sql = "insert into solver_result (solver_id, return_code, duration) values (%d, %d, %f);" % (id, returnCode, duration)

            self.cursor.execute(sql)
        except Exception as e:
            print("DB.addSolverResult::error execute \"{}\" error: {}".format(sql, e))
            self.dbAvailable = False

    def initRando(self):
        if self.dbAvailable == False:
            return None

        try:
            sql = "insert into randomizer (action_time) values (now());"
            self.cursor.execute(sql)
            return self.cursor.lastrowid
        except Exception as e:
            print("DB.initRando::error execute: {} error: {}".format(sql, e))
            self.dbAvailable = False

    def addRandoParams(self, id, params):
        if self.dbAvailable == False:
            return None

        ignoreParams = ['paramsFileTarget', 'complexity']

        try:
            sql = "insert into randomizer_params values (%d, '%s', '%s');"
            for (name, value) in params.items():
                if name in ignoreParams:
                    continue
                self.cursor.execute(sql % (id, name, value))
        except Exception as e:
            print("DB.addRandoParams::error execute: {}".format(e))
            self.dbAvailable = False

    def updateRandoParams(self, id, params):
        if self.dbAvailable == False:
            return None

        try:
            sql = "update randomizer_params set value = '%s' where randomizer_id = %d and name = '%s';"
            for (name, value) in params.items():
                self.cursor.execute(sql % (value, id, name))
        except Exception as e:
            print("DB.updateRandoParams::error execute: {}".format(e))
            self.dbAvailable = False

    def addRandoResult(self, id, returnCode, duration, msg):
        if self.dbAvailable == False:
            return None

        def escapeMsg(msg):
            return msg.replace("'", "''")

        try:
            msg = escapeMsg(msg)
            sql = "insert into randomizer_result (randomizer_id, return_code, duration, error_msg) values (%d, %d, %f, '%s');"
            self.cursor.execute(sql % (id, returnCode, duration, msg))
        except Exception as e:
            print("DB.addRandoResult::error execute \"{}\" error: {}".format(sql, e))
            self.dbAvailable = False

    def addRandoUploadResult(self, id, guid, fileName):
        if self.dbAvailable == False:
            return None

        try:
            sql = """
update randomizer set upload_status = 'local', filename = '%s', guid = '%s'
where id = %s;"""
            self.cursor.execute(sql % (fileName, guid, id))
        except Exception as e:
            print("DB.addRandoUploadResult::error execute \"{}\" error: {}".format(sql, e))
            self.dbAvailable = False

    def addPresetAction(self, preset, action):
        if self.dbAvailable == False:
            return None

        try:
            sql = "insert into preset_action (preset, action_time, action) values ('%s', now(), '%s');"
            self.cursor.execute(sql % (preset, action))
        except Exception as e:
            print("DB.initPresets::error execute: {} error: {}".format(sql, e))
            self.dbAvailable = False

    def addISolver(self, preset, romFileName):
        if self.dbAvailable == False:
            return None

        try:
            sql = "insert into isolver (init_time, preset, romFileName) values (now(), '%s', '%s');"
            self.cursor.execute(sql % (preset, romFileName))
        except Exception as e:
            print("DB.addISolver::error execute: {} error: {}".format(sql, e))
            self.dbAvailable = False

    # read data
    def execSelect(self, sql, params=None):
        if self.dbAvailable == False:
            return None

        try:
            if params == None:
                self.cursor.execute(sql)
            else:
                self.cursor.execute(sql % params)
            return self.cursor.fetchall()
        except Exception as e:
            print("DB.execSelect::error execute \"{}\" error: {}".format(sql, e))
            self.dbAvailable = False

    def getUsage(self, table, weeks):
        if self.dbAvailable == False:
            return None

        sql = "select date(action_time), count(*) from {} where action_time > DATE_SUB(CURDATE(), INTERVAL %d WEEK) group by date(action_time) order by 1;".format(table)
        return self.execSelect(sql, (weeks,))

    def getSolverUsage(self, weeks):
        return self.getUsage('solver', weeks)

    def getRandomizerUsage(self, weeks):
        return self.getUsage('randomizer', weeks)

    def getSolverPresets(self, weeks):
        if self.dbAvailable == False:
            return None

        sql = "select distinct(sp.preset) from solver s join solver_params sp on s.id = sp.solver_id where s.action_time > DATE_SUB(CURDATE(), INTERVAL %d WEEK);"
        presets = self.execSelect(sql, (weeks,))
        if presets == None:
            return None

        # db returns tuples
        presets = [preset[0] for preset in presets]

        # pivot
        sql = "SELECT date(s.action_time)"
        for preset in presets:
            sql += ", SUM(CASE WHEN sp.preset = '{}' THEN 1 ELSE 0 END) AS count_{}".format(preset, preset)
        sql += " FROM solver s join solver_params sp on s.id = sp.solver_id where s.action_time > DATE_SUB(CURDATE(), INTERVAL {} WEEK) GROUP BY date(s.action_time);".format(weeks)

        return (presets, self.execSelect(sql))

    def getSolverResults(self, weeks):
        if self.dbAvailable == False:
            return None

        sql = "select date(s.action_time), sr.return_code, count(*) from solver s join solver_result sr on s.id = sr.solver_id where s.action_time > DATE_SUB(CURDATE(), INTERVAL %d WEEK) group by date(s.action_time), sr.return_code order by 1;"
        return self.execSelect(sql, (weeks,))

    def getSolverDurations(self, weeks):
        if self.dbAvailable == False:
            return None

        sql = "select s.action_time, sr.duration from solver s join solver_result sr on s.id = sr.solver_id where s.action_time > DATE_SUB(CURDATE(), INTERVAL %d WEEK) order by 1;"
        return self.execSelect(sql, (weeks,))

    def getRandomizerPresets(self, weeks):
        if self.dbAvailable == False:
            return None

        sql = "select distinct(value) from randomizer r join randomizer_params rp on r.id = rp.randomizer_id where rp.name = 'preset' and r.action_time > DATE_SUB(CURDATE(), INTERVAL %d WEEK);"
        presets = self.execSelect(sql, (weeks,))
        if presets == None:
            return None

        # db returns tuples
        presets = [preset[0] for preset in presets]

        # pivot
        sql = "SELECT date(r.action_time)"
        for preset in presets:
            sql += ", SUM(CASE WHEN rp.value = '{}' THEN 1 ELSE 0 END) AS count_{}".format(preset, preset)
        sql += " FROM randomizer r join randomizer_params rp on r.id = rp.randomizer_id where rp.name = 'preset' and r.action_time > DATE_SUB(CURDATE(), INTERVAL {} WEEK) GROUP BY date(r.action_time);".format(weeks)

        return (presets, self.execSelect(sql))

    def getRandomizerDurations(self, weeks):
        if self.dbAvailable == False:
            return None

        sql = "select r.action_time, rr.duration from randomizer r join randomizer_result rr on r.id = rr.randomizer_id where r.action_time > DATE_SUB(CURDATE(), INTERVAL %d WEEK) order by 1;"
        return self.execSelect(sql, (weeks,))

    def getSolverData(self, weeks):
        if self.dbAvailable == False:
            return None

        # return all data csv style
        sql = """select sr.return_code, s.id, s.action_time,
sp.romFileName, sp.preset, sp.difficultyTarget, sp.pickupStrategy,
sr.return_code, lpad(round(sr.duration, 2), 5, '0'), sr.difficulty, sr.knows_used, sr.knows_known, sr.items_ok, sr.len_remainTry, sr.len_remainMajors, sr.len_remainMinors, sr.len_skippedMajors, sr.len_unavailMajors,
sci.collected_items,
sif.forbidden_items
from solver s
  left join solver_params sp on s.id = sp.solver_id
  left join solver_result sr on s.id = sr.solver_id
  left join (select solver_id, group_concat(\"(\", item, \", \", count, \")\" order by item) as collected_items from solver_collected_items group by solver_id) sci on s.id = sci.solver_id
  left join (select solver_id, group_concat(item order by item) as forbidden_items from solver_items_forbidden group by solver_id) sif on s.id = sif.solver_id
where s.action_time > DATE_SUB(CURDATE(), INTERVAL %d WEEK)
order by s.id;"""

        header = ["id", "actionTime", "romFileName", "preset", "difficultyTarget", "pickupStrategy", "returnCode", "duration", "difficulty", "knowsUsed", "knowsKnown", "itemsOk", "remainTry", "remainMajors", "remainMinors", "skippedMajors", "unavailMajors", "collectedItems", "forbiddenItems"]
        return (header, self.execSelect(sql, (weeks,)))

    def getRandomizerData(self, weeks):
        if self.dbAvailable == False:
            return None

        # now that we store random multi select values we reach a mysql limit with group_concat.
        # solution:
        # SET GLOBAL group_concat_max_len=8192;
        # but we're not super user on production, so set it at session level
        sql = "SET SESSION group_concat_max_len=8192";
        try:
            self.cursor.execute(sql)
        except Exception as e:
            print("DB.getRandomizerData::error execute \"{}\" error: {}".format(sql, e))
            self.dbAvailable = False
            return None

        sql = """select rr.return_code,
r.id, r.action_time, rr.return_code, lpad(round(rr.duration, 2), 5, '0'), rr.error_msg,
rp.params
from randomizer r
  left join (select randomizer_id, group_concat(\"'\", name, \"': '\", value, \"'\" order by name) as params from randomizer_params group by randomizer_id) rp on r.id = rp.randomizer_id
  left join randomizer_result rr on r.id = rr.randomizer_id
where r.action_time > DATE_SUB(CURDATE(), INTERVAL %d WEEK)
order by r.id;"""

        data = self.execSelect(sql, (weeks,))
        if data == None:
            return None

        outData = []
        paramsSet = set()
        for row in data:
            # use a dict for the parameters which are in the last column
            params = row[-1]
            dictParams = eval('{' + params + '}')
            outData.append(row[0:-1] + (dictParams,))
            paramsSet.update(dictParams.keys())

        # custom sort of the params
        paramsHead = []
        for param in ['seed', 'preset', 'startLocation', 'startLocationMultiSelect', 'areaRandomization', 'areaLayout', 'lightAreaRandomization', 'bossRandomization', 'majorsSplit', 'majorsSplitMultiSelect', 'progressionSpeed', 'progressionSpeedMultiSelect', 'maxDifficulty', 'morphPlacement', 'morphPlacementMultiSelect', 'suitsRestriction', 'energyQty', 'energyQtyMultiSelect', 'minorQty', 'missileQty', 'superQty', 'powerBombQty', 'progressionDifficulty', 'progressionDifficultyMultiSelect', 'escapeRando', 'removeEscapeEnemies', 'funCombat', 'funMovement', 'funSuits', 'hideItems', 'strictMinors']:
            if param in paramsSet:
                paramsHead.append(param)
                paramsSet.remove(param)

        header = ["id", "actionTime", "returnCode", "duration", "errorMsg"]
        return (header, outData, paramsHead + sorted(list(paramsSet)))

    def getRandomizerSeedParams(self, randomizer_id):
        if self.dbAvailable == False:
            return None

        sql = "select group_concat(\"--\", name, \" \", case when value = 'None' then \"\" else value end order by name separator ' ') from randomizer_params where randomizer_id = %d;"
        data = self.execSelect(sql, (randomizer_id,))
        if data == None:
            return ""
        else:
            return data[0][0]

    def getGeneratedSeeds(self, preset):
        if self.dbAvailable == False:
            return None

        sql = "select count(*) from randomizer_params where name = 'preset' and value = '%s';"
        data = self.execSelect(sql, (preset,))
        if data == None:
            return 0
        else:
            return data[0][0]

    def getPresetLastActionDate(self, preset):
        if self.dbAvailable == False:
            return None

        sql = "select max(action_time) from preset_action where preset = '%s';"
        data = self.execSelect(sql, (preset,))
        if data == None:
            return 'N/A'
        data = data[0][0] if data[0][0] != None else 'N/A'
        return data

        return self.execSelect(sql % (id,))

    def getSeedInfo(self, key):
        # key is id from randomizer table
        if self.dbAvailable == False:
            return None

        sql = """
select 'upload_status', upload_status
from randomizer
where guid = '%s'
union all
select 'filename', filename
from randomizer
where guid = '%s'
union all
select 'time', action_time
from randomizer
where guid = '%s'
union all
select name, value
from randomizer_params
where randomizer_id = (select id from randomizer where guid = '%s')
order by 1;"""

        return self.execSelect(sql % (key, key, key, key))

    def getSeedIpsInfo(self, key):
        # key is id from randomizer table
        if self.dbAvailable == False:
            return None

        sql = """select upload_status, filename from randomizer where guid = '%s';"""

        return self.execSelect(sql % (key,))

    def updateSeedUploadStatus(self, key, newStatus):
        # key is id from randomizer table
        if self.dbAvailable == False:
            return None

        try:
            sql = """update randomizer set upload_status = '%s' where guid = '%s';"""
            self.cursor.execute(sql % (newStatus, key))
        except Exception as e:
            print("DB.updateSeedUploadStatus::error execute: {}".format(e))
            self.dbAvailable = False

    def getISolver(self, weeks):
        if self.dbAvailable == False:
            return None

        sql = "select distinct(preset) from isolver where init_time > DATE_SUB(CURDATE(), INTERVAL %d WEEK);"
        presets = self.execSelect(sql, (weeks,))
        if presets == None:
            return None

        # db returns tuples
        presets = [preset[0] for preset in presets]

        # pivot
        sql = "SELECT date(init_time)"
        for preset in presets:
            sql += ", SUM(CASE WHEN preset = '{}' THEN 1 ELSE 0 END) AS count_{}".format(preset, preset)
        sql += " FROM isolver where init_time > DATE_SUB(CURDATE(), INTERVAL {} WEEK) GROUP BY date(init_time);".format(weeks)

        return (presets, self.execSelect(sql))

    def getISolverData(self, weeks):
        if self.dbAvailable == False:
            return None

        # return all data csv style
        sql = """select 0, init_time, preset, romFileName
from isolver
where init_time > DATE_SUB(CURDATE(), INTERVAL %d WEEK)
order by init_time;"""

        header = ["initTime", "preset", "romFileName"]
        return (header, self.execSelect(sql, (weeks,)))

    @staticmethod
    def dumpExtStatsItems(parameters, locsItems, sqlFile):
        sql = """insert into extended_stats (preset, area, boss, majorsSplit, progSpeed, morphPlacement, suitsRestriction, progDiff, superFunMovement, superFunCombat, superFunSuit, gravityBehaviour, nerfedCharge, maxDifficulty, startAP, count)
values
('%s', %s, %s, '%s', '%s', '%s', %s, '%s', %s, %s, %s, '%s', %s, '%s', '%s', 1)
on duplicate key update id=LAST_INSERT_ID(id), count = count + 1;
set @last_id = last_insert_id();
"""

        sqlFile.write(sql % (parameters['preset'], parameters['area'], parameters['boss'], parameters['majorsSplit'], parameters['progSpeed'], parameters['morphPlacement'], parameters['suitsRestriction'], parameters['progDiff'], parameters['superFunMovement'], parameters['superFunCombat'], parameters['superFunSuit'], parameters['gravityBehaviour'], parameters['nerfedCharge'], parameters['maxDifficulty'], parameters['startAP']))

        for (location, item) in locsItems.items():
            if item == 'Boss':
                continue
            # we can't have special chars in columns names
            location = removeChars(location, " ,()-")
            sql = "insert into item_locs (ext_id, item, {}) values (@last_id, '%s', 1) on duplicate key update {} = {} + 1;\n".format(location, location, location)

            sqlFile.write(sql % (item,))

    @staticmethod
    def dumpExtStatsSolver(difficulty, techniques, solverStats, step, sqlFile):
        # use @last_id defined by the randomizer

        if step == 1:
            # get difficulty column
            if difficulty < medium:
                column = "easy"
            elif difficulty < hard:
                column = "medium"
            elif difficulty < harder:
                column = "hard"
            elif difficulty < hardcore:
                column = "harder"
            elif difficulty < mania:
                column = "hardcore"
            else:
                column = "mania"

            sql = "insert into difficulties (ext_id, {}) values (@last_id, 1) on duplicate key update {} = {} + 1;\n".format(column, column, column)
            sqlFile.write(sql)

            for technique in techniques:
                sql = "insert into techniques (ext_id, technique, count) values (@last_id, '%s', 1) on duplicate key update count = count + 1;\n"
                sqlFile.write(sql % (technique,))
        else:
            for (stat, value) in solverStats.items():
                sql = "insert into solver_stats (ext_id, name, value) values (@last_id, '%s', %d);\n"
                sqlFile.write(sql % (stat, value))

            # to avoid // issues
            sqlFile.write("commit;\n")

    def getExtStat(self, parameters):
        if self.dbAvailable == False:
            return (None, None, None, None)

        sqlItems = """select sum(e.count), i.item, round(100*sum(i.EnergyTankGauntlet)/sum(e.count), 1), round(100*sum(i.Bomb)/sum(e.count), 1), round(100*sum(i.EnergyTankTerminator)/sum(e.count), 1), round(100*sum(i.ReserveTankBrinstar)/sum(e.count), 1), round(100*sum(i.ChargeBeam)/sum(e.count), 1), round(100*sum(i.MorphingBall)/sum(e.count), 1), round(100*sum(i.EnergyTankBrinstarCeiling)/sum(e.count), 1), round(100*sum(i.EnergyTankEtecoons)/sum(e.count), 1), round(100*sum(i.EnergyTankWaterway)/sum(e.count), 1), round(100*sum(i.EnergyTankBrinstarGate)/sum(e.count), 1), round(100*sum(i.XRayScope)/sum(e.count), 1), round(100*sum(i.Spazer)/sum(e.count), 1), round(100*sum(i.EnergyTankKraid)/sum(e.count), 1), round(100*sum(i.Kraid)/sum(e.count), 1), round(100*sum(i.VariaSuit)/sum(e.count), 1), round(100*sum(i.IceBeam)/sum(e.count), 1), round(100*sum(i.EnergyTankCrocomire)/sum(e.count), 1), round(100*sum(i.HiJumpBoots)/sum(e.count), 1), round(100*sum(i.GrappleBeam)/sum(e.count), 1), round(100*sum(i.ReserveTankNorfair)/sum(e.count), 1), round(100*sum(i.SpeedBooster)/sum(e.count), 1), round(100*sum(i.WaveBeam)/sum(e.count), 1), round(100*sum(i.Ridley)/sum(e.count), 1), round(100*sum(i.EnergyTankRidley)/sum(e.count), 1), round(100*sum(i.ScrewAttack)/sum(e.count), 1), round(100*sum(i.EnergyTankFirefleas)/sum(e.count), 1), round(100*sum(i.ReserveTankWreckedShip)/sum(e.count), 1), round(100*sum(i.EnergyTankWreckedShip)/sum(e.count), 1), round(100*sum(i.Phantoon)/sum(e.count), 1), round(100*sum(i.RightSuperWreckedShip)/sum(e.count), 1), round(100*sum(i.GravitySuit)/sum(e.count), 1), round(100*sum(i.EnergyTankMamaturtle)/sum(e.count), 1), round(100*sum(i.PlasmaBeam)/sum(e.count), 1), round(100*sum(i.ReserveTankMaridia)/sum(e.count), 1), round(100*sum(i.SpringBall)/sum(e.count), 1), round(100*sum(i.EnergyTankBotwoon)/sum(e.count), 1), round(100*sum(i.Draygon)/sum(e.count), 1), round(100*sum(i.SpaceJump)/sum(e.count), 1), round(100*sum(i.MotherBrain)/sum(e.count), 1), round(100*sum(i.PowerBombCrateriasurface)/sum(e.count), 1), round(100*sum(i.MissileoutsideWreckedShipbottom)/sum(e.count), 1), round(100*sum(i.MissileoutsideWreckedShiptop)/sum(e.count), 1), round(100*sum(i.MissileoutsideWreckedShipmiddle)/sum(e.count), 1), round(100*sum(i.MissileCrateriamoat)/sum(e.count), 1), round(100*sum(i.MissileCrateriabottom)/sum(e.count), 1), round(100*sum(i.MissileCrateriagauntletright)/sum(e.count), 1), round(100*sum(i.MissileCrateriagauntletleft)/sum(e.count), 1), round(100*sum(i.SuperMissileCrateria)/sum(e.count), 1), round(100*sum(i.MissileCrateriamiddle)/sum(e.count), 1), round(100*sum(i.PowerBombgreenBrinstarbottom)/sum(e.count), 1), round(100*sum(i.SuperMissilepinkBrinstar)/sum(e.count), 1), round(100*sum(i.MissilegreenBrinstarbelowsupermissile)/sum(e.count), 1), round(100*sum(i.SuperMissilegreenBrinstartop)/sum(e.count), 1), round(100*sum(i.MissilegreenBrinstarbehindmissile)/sum(e.count), 1), round(100*sum(i.MissilegreenBrinstarbehindreservetank)/sum(e.count), 1), round(100*sum(i.MissilepinkBrinstartop)/sum(e.count), 1), round(100*sum(i.MissilepinkBrinstarbottom)/sum(e.count), 1), round(100*sum(i.PowerBombpinkBrinstar)/sum(e.count), 1), round(100*sum(i.MissilegreenBrinstarpipe)/sum(e.count), 1), round(100*sum(i.PowerBombblueBrinstar)/sum(e.count), 1), round(100*sum(i.MissileblueBrinstarmiddle)/sum(e.count), 1), round(100*sum(i.SuperMissilegreenBrinstarbottom)/sum(e.count), 1), round(100*sum(i.MissileblueBrinstarbottom)/sum(e.count), 1), round(100*sum(i.MissileblueBrinstartop)/sum(e.count), 1), round(100*sum(i.MissileblueBrinstarbehindmissile)/sum(e.count), 1), round(100*sum(i.PowerBombredBrinstarsidehopperroom)/sum(e.count), 1), round(100*sum(i.PowerBombredBrinstarspikeroom)/sum(e.count), 1), round(100*sum(i.MissileredBrinstarspikeroom)/sum(e.count), 1), round(100*sum(i.MissileKraid)/sum(e.count), 1), round(100*sum(i.Missilelavaroom)/sum(e.count), 1), round(100*sum(i.MissilebelowIceBeam)/sum(e.count), 1), round(100*sum(i.MissileaboveCrocomire)/sum(e.count), 1), round(100*sum(i.MissileHiJumpBoots)/sum(e.count), 1), round(100*sum(i.EnergyTankHiJumpBoots)/sum(e.count), 1), round(100*sum(i.PowerBombCrocomire)/sum(e.count), 1), round(100*sum(i.MissilebelowCrocomire)/sum(e.count), 1), round(100*sum(i.MissileGrappleBeam)/sum(e.count), 1), round(100*sum(i.MissileNorfairReserveTank)/sum(e.count), 1), round(100*sum(i.MissilebubbleNorfairgreendoor)/sum(e.count), 1), round(100*sum(i.MissilebubbleNorfair)/sum(e.count), 1), round(100*sum(i.MissileSpeedBooster)/sum(e.count), 1), round(100*sum(i.MissileWaveBeam)/sum(e.count), 1), round(100*sum(i.MissileGoldTorizo)/sum(e.count), 1), round(100*sum(i.SuperMissileGoldTorizo)/sum(e.count), 1), round(100*sum(i.MissileMickeyMouseroom)/sum(e.count), 1), round(100*sum(i.MissilelowerNorfairabovefireflearoom)/sum(e.count), 1), round(100*sum(i.PowerBomblowerNorfairabovefireflearoom)/sum(e.count), 1), round(100*sum(i.PowerBombPowerBombsofshame)/sum(e.count), 1), round(100*sum(i.MissilelowerNorfairnearWaveBeam)/sum(e.count), 1), round(100*sum(i.MissileWreckedShipmiddle)/sum(e.count), 1), round(100*sum(i.MissileGravitySuit)/sum(e.count), 1), round(100*sum(i.MissileWreckedShiptop)/sum(e.count), 1), round(100*sum(i.SuperMissileWreckedShipleft)/sum(e.count), 1), round(100*sum(i.MissilegreenMaridiashinespark)/sum(e.count), 1), round(100*sum(i.SuperMissilegreenMaridia)/sum(e.count), 1), round(100*sum(i.MissilegreenMaridiatatori)/sum(e.count), 1), round(100*sum(i.SuperMissileyellowMaridia)/sum(e.count), 1), round(100*sum(i.MissileyellowMaridiasupermissile)/sum(e.count), 1), round(100*sum(i.MissileyellowMaridiafalsewall)/sum(e.count), 1), round(100*sum(i.MissileleftMaridiasandpitroom)/sum(e.count), 1), round(100*sum(i.MissilerightMaridiasandpitroom)/sum(e.count), 1), round(100*sum(i.PowerBombrightMaridiasandpitroom)/sum(e.count), 1), round(100*sum(i.MissilepinkMaridia)/sum(e.count), 1), round(100*sum(i.SuperMissilepinkMaridia)/sum(e.count), 1), round(100*sum(i.MissileDraygon)/sum(e.count), 1)
from extended_stats e join item_locs i on e.id = i.ext_id
where item not in ('Nothing', 'NoEnergy', 'ETank', 'Reserve', 'Kraid', 'Phantoon', 'Draygon', 'Ridley', 'MotherBrain')
{}
group by i.item
order by i.item;"""

        sqlTechniques = """select t.technique, round(100*sum(t.count)/sum(e.count), 1)
from extended_stats e
  join techniques t on e.id = t.ext_id
where 1 = 1
{}
group by t.technique;"""

        sqlDifficulties = """
select sum(d.easy), sum(d.medium), sum(d.hard), sum(d.harder), sum(d.hardcore), sum(d.mania)
from extended_stats e
  join difficulties d on e.id = d.ext_id
where 1 = 1
{};"""

        sqlSolverStats = """
select s.name, s.value, round(count(*) * 100 / e.count, 1)
from extended_stats e
  join solver_stats s on e.id = s.ext_id
where 1 = 1
{}
group by s.name, s.value
order by 1,2;"""

        (where, sqlParams) = self.getWhereClause(parameters)

        items = self.execSelect(sqlItems.format(where), tuple(sqlParams))

        techniques = self.execSelect(sqlTechniques.format(where), tuple(sqlParams))
        # transform techniques into a dict
        techOut = {}
        if techniques != None:
            for technique in techniques:
                techOut[technique[0]] = technique[1]

        difficulties = self.execSelect(sqlDifficulties.format(where), tuple(sqlParams))
        if difficulties != None:
            difficulties = difficulties[0]

            # check if all values are null
            if difficulties.count(None) == len(difficulties):
                difficulties = []

        solverStats = self.execSelect(sqlSolverStats.format(where), tuple(sqlParams))
        solverStatsOut = {}
        if solverStats != None:
            for stat in solverStats:
                (name, value, count) = stat
                if name not in solverStatsOut:
                    solverStatsOut[name] = []
                solverStatsOut[name].append((value, count))

        return (items, techOut, difficulties, solverStatsOut)

    def getProgSpeedStat(self, parameters):
        if self.dbAvailable == False:
            return None

        sqlSolverStats = """
select s.name, s.value, round(count(*) * 100 / e.count, 1)
from extended_stats e
  join solver_stats s on e.id = s.ext_id
where 1 = 1
{}
group by s.name, s.value
order by 1,2;"""

        (where, sqlParams) = self.getWhereClause(parameters)

        solverStats = self.execSelect(sqlSolverStats.format(where), tuple(sqlParams))
        solverStatsOut = {}
        if solverStats != None:
            for stat in solverStats:
                (name, value, count) = stat
                if name not in solverStatsOut:
                    solverStatsOut[name] = []
                solverStatsOut[name].append((value, count))

        return solverStatsOut

    def getWhereClause(self, parameters):
        where = """and e.preset = '%s' and e.area = %s and e.boss = %s and e.gravityBehaviour = '%s' and e.nerfedCharge = %s """

        sqlParams = [parameters['preset'], parameters['area'], parameters['boss'], parameters['gravityBehaviour'], parameters['nerfedCharge']]

        if parameters["maxDifficulty"] != "random":
            where += """and e.maxDifficulty = '%s' """
            sqlParams.append(parameters['maxDifficulty'])

        if parameters["startAP"] != "random":
            where += """and e.startAP = '%s' """
            sqlParams.append(parameters['startAP'])

        if parameters['majorsSplit'] != "random":
            where += """and e.majorsSplit = '%s' """
            sqlParams.append(parameters['majorsSplit'])

        if parameters['progSpeed'] != "random":
            if type(parameters['progSpeed']) != list:
                where += """and e.progSpeed = '%s' """
                sqlParams.append(parameters['progSpeed'])
            else:
                where += """and e.progSpeed in ('%s') """
                sqlParams.append("','".join(parameters['progSpeed']))

        if parameters['morphPlacement'] != "random":
            where += """and e.morphPlacement = '%s' """
            sqlParams.append(parameters['morphPlacement'])

        if parameters['suitsRestriction'] != "random":
            where += """and e.suitsRestriction = %s """
            sqlParams.append(parameters['suitsRestriction'])

        if parameters['progDiff'] != "random":
            where += """and e.progDiff = '%s' """
            sqlParams.append(parameters['progDiff'])

        if parameters['superFunMovement'] != "random":
            where += """and e.superFunMovement = %s """
            sqlParams.append(parameters['superFunMovement'])

        if parameters['superFunCombat'] != "random":
            where += """and e.superFunCombat = %s """
            sqlParams.append(parameters['superFunCombat'])

        if parameters['superFunSuit'] != "random":
            where += """and e.superFunSuit = %s """
            sqlParams.append(parameters['superFunSuit'])

        return (where, sqlParams)

    def getPlandos(self):
        if self.dbAvailable == False:
            return None

        try:
            sql = "select re.plando_name, re.init_time, re.author, re.long_desc, re.suggested_preset, re.download_count, (select sum(ra.rating)/count(1) from plando_rating ra where ra.plando_name = re.plando_name), (select count(1) from plando_rating ra where ra.plando_name = re.plando_name) from plando_repo re;"
            return self.execSelect(sql)
        except Exception as e:
            print("DB.getPlandos::error execute: {} error: {}".format(sql, e))
            self.dbAvailable = False

    def getPlando(self, plandoName):
        if self.dbAvailable == False:
            return None

        try:
            sql = "select re.plando_name, re.init_time, re.author, re.long_desc, re.suggested_preset, re.download_count, (select sum(ra.rating)/count(1) from plando_rating ra where ra.plando_name = re.plando_name), (select count(1) from plando_rating ra where ra.plando_name = re.plando_name) from plando_repo re where re.plando_name = '%s';"
            return self.execSelect(sql, (plandoName,))
        except Exception as e:
            print("DB.getPlando::error execute: {} error: {}".format(sql, e))
            self.dbAvailable = False

    def getPlandoCount(self):
        if self.dbAvailable == False:
            return None

        try:
            sql = "select count(1) from plando_repo;"
            return self.execSelect(sql)
        except Exception as e:
            print("DB.getPlandoCount::error execute: {} error: {}".format(sql, e))
            self.dbAvailable = False

    def getPlandoKey(self, plandoName):
        if self.dbAvailable == False:
            return None

        try:
            sql = "select update_key from plando_repo where plando_name = '%';"
            return self.execSelect(sql, (plandoName,))
        except Exception as e:
            print("DB.getPlandoKey::error execute: {} error: {}".format(sql, e))
            self.dbAvailable = False

    def getPlandoIpsMaxSize(self, plandoName):
        if self.dbAvailable == False:
            return None

        try:
            sql = "select ips_max_size from plando_repo where plando_name = '%s';"
            return self.execSelect(sql, (plandoName,))
        except Exception as e:
            print("DB.getPlandoIpsMaxSize::error execute: {} error: {}".format(sql, e))
            self.dbAvailable = False

    def getPlandoRate(self, plandoName):
        if self.dbAvailable == False:
            return None

        try:
            sql = "select count(1), sum(rating)/count(1) from plando_rating where plando_name = '%s';"
            return self.execSelect(sql, (plandoName,))
        except Exception as e:
            print("DB.getPlandoRate::error execute: {} error: {}".format(sql, e))
            self.dbAvailable = False

    def insertPlando(self, params):
        if self.dbAvailable == False:
            return None

        try:
            sql = "insert into plando_repo (plando_name, init_time, author, long_desc, suggested_preset, update_key, ips_max_size) values ('%s', now(), '%s', '%s', '%s', '%s', %d);"
            self.cursor.execute(sql % params)
            self.commit()
        except Exception as e:
            print("DB.insertPlando::error execute: {} error: {}".format(sql, e))
            self.dbAvailable = False

    def updatePlandoAll(self, params):
        if self.dbAvailable == False:
            return None

        try:
            sql = "update plando_repo set init_time = now(), author = '%s', long_desc = '%s', suggested_preset = '%s', ips_max_size = %d where plando_name = '%s'"
            self.cursor.execute(sql % params)
            self.commit()
        except Exception as e:
            print("DB.updatePlandoAll::error execute: {} error: {}".format(sql, e))
            self.dbAvailable = False

    def updatePlandoMeta(self, params):
        if self.dbAvailable == False:
            return None

        try:
            sql = "update plando_repo set author = '%s', long_desc = '%s', suggested_preset = '%s' where plando_name = '%s'"
            self.cursor.execute(sql % params)
            self.commit()
        except Exception as e:
            print("DB.updatePlandoMeta::error execute: {} error: {}".format(sql, e))
            self.dbAvailable = False

    def alreadyRated(self, plandoName, ip):
        if self.dbAvailable == False:
            return None

        try:
            sql = "select 1 from plando_rating where plando_name = '%s' and ipv4 = inet_aton('%s');"
            return self.execSelect(sql % (plandoName, ip))
        except Exception as e:
            print("DB.alreadyRated::error execute: {} error: {}".format(sql, e))
            self.dbAvailable = False

    def addRating(self, plandoName, rating, ip):
        if self.dbAvailable == False:
            return None

        try:
            sql = """
REPLACE INTO plando_rating
    (plando_name, rating, ipv4)
VALUES ('%s', %d, inet_aton('%s'));"""
            self.cursor.execute(sql % (plandoName, rating, ip))
            self.commit()
        except Exception as e:
            print("DB.addRating::error execute: {} error: {}".format(sql, e))
            self.dbAvailable = False

    def increaseDownloadCount(self, plandoName):
        if self.dbAvailable == False:
            return None

        try:
            sql = "update plando_repo set download_count = download_count+1 where plando_name = '%s';"
            self.cursor.execute(sql % (plandoName,))
            self.commit()
        except Exception as e:
            print("DB.increaseDownloadCount::error execute: {} error: {}".format(sql, e))
            self.dbAvailable = False

    def isValidPlandoKey(self, plandoName, key):
        if self.dbAvailable == False:
            return None

        try:
            sql = "select 1 from plando_repo where plando_name = '%s' and update_key = '%s';"
            return self.execSelect(sql % (plandoName, key))
        except Exception as e:
            print("DB.isValidPlandoKey::error execute: {} error: {}".format(sql, e))
            self.dbAvailable = False

    def deletePlando(self, plandoName):
        if self.dbAvailable == False:
            return None

        try:
            sql = "delete from plando_repo where plando_name = '%s';"
            self.cursor.execute(sql % (plandoName,))
            self.commit()
        except Exception as e:
            print("DB.deletePlando::error execute: {} error: {}".format(sql, e))
            self.dbAvailable = False

    def deletePlandoRating(self, plandoName):
        if self.dbAvailable == False:
            return None

        try:
            sql = "delete from plando_rating where plando_name = '%s';"
            self.cursor.execute(sql % (plandoName,))
            self.commit()
        except Exception as e:
            print("DB.deletePlandoRating::error execute: {} error: {}".format(sql, e))
            self.dbAvailable = False
