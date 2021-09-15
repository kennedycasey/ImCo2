import sqlite3


class ImcoDb(object):

    def __init__(self, db_path, codes):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        self._ensure_schema(codes)

    def get(self):
        return self.connection

    def get_cursor(self):
        return self.connection.cursor()

    def load_state(self):
        curs = self.get_cursor()
        q = '''SELECT * FROM `state`'''
        curs.execute(q)
        return dict(curs)

    def store_state(self, state):
        conn = self.get()
        curs = conn.cursor()
        q = '''INSERT OR REPLACE INTO `state` (Var, Val) VALUES (?, ?)'''
        curs.executemany(q, ((k, str(v)) for k, v in state.items()))
        conn.commit()

    def load_image_rows(self, dir_name):
        rows = self.iterate_image_rows(dir_name)
        return dict((r['Image'], dict(r)) for r in rows)

    def iterate_image_rows(self, dir_name=None):
        curs = self.get_cursor()
        args = {}
        if dir_name is not None:
            dir_clause = '''WHERE `Dir` = :dir'''
            args['dir'] = dir_name
        else:
            dir_clause = ''
        q = '''
            SELECT * FROM `codes`
            {dir_clause}
            ORDER BY Dir ASC, Image ASC
            '''.format(dir_clause=dir_clause)
        curs.execute(q, args)
        return curs

    def store_image_rows(self, images, codes):
        conn = self.get()
        curs = conn.cursor()
        code_columns = [c.code for c in codes]
        columns_str = ', '.join(code_columns)
        qmarks = ', '.join(['?'] * (3 + len(code_columns)))
        q = '''INSERT OR REPLACE INTO `codes` (Dir, Image, Modified, {})
               VALUES ({})'''.format(columns_str, qmarks)
        values = []
        for img in images:
            code_values = [c.to_db(img.codes[c.code]) for c in codes]
            v = tuple([img.dir, img.name, img.timestamp] + code_values)
            values.append(v)
        curs.executemany(q, values)
        conn.commit()

    def _ensure_schema(self, codes):
        conn = self.get()
        curs = conn.cursor()
        q = '''
            CREATE TABLE IF NOT EXISTS `state` (
                Var TEXT PRIMARY KEY,
                Val TEXT
            )'''
        curs.execute(q)
        # TODO: Change schema so that we don't need the codes
        colnames = [c.code for c in codes]
        col_defs = ', '.join('{} TEXT'.format(cn) for cn in colnames)
        q = '''
            CREATE TABLE IF NOT EXISTS `codes` (
                Dir TEXT,
                Image TEXT,
                Modified TEXT CURRENT_TIMESTAMP,
                {},
                PRIMARY KEY (Dir, Image)
            )'''.format(col_defs)
        curs.execute(q)
        conn.commit()
