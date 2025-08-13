import asyncpg


class Database:
    def __init__(self, connector: asyncpg.pool.Pool):
        self.pool = connector

    async def get_time(self, date):
        query = 'SELECT time FROM bot_book_consultation WHERE date = $1'
        result = await self.pool.fetch(query, date)
        times = [row['time'] for row in result]
        return times

    async def add_info(self, user_id, user_name, phone_number, date, time, problem_descr):
        await self.pool.execute('INSERT INTO bot_book_consultation (user_id, user_name, phone_number, date, time, problem_descr) '
                                'VALUES($1, $2, $3, $4, $5, $6)', user_id, user_name, phone_number, date, time, problem_descr)


    async def add_question(self, user_id, user_name, problem_descr):
        await self.pool.execute('INSERT INTO bot_ask_lawyer (user_id, user_name, problem_descr) '
                                'VALUES($1, $2, $3)', user_id, user_name, problem_descr)

    async def get_consult(self):
        query = 'SELECT * FROM bot_book_consultation ORDER BY date ASC, time ASC'
        result = await self.pool.fetch(query)
        return result

    async def get_questions(self):
        query = 'SELECT * FROM bot_ask_lawyer WHERE execution = FALSE'
        result = await self.pool.fetch(query)
        return result

    async def get_question_by_id(self, question_id: int):
        query = "SELECT * FROM bot_ask_lawyer WHERE id = $1"
        return await self.pool.fetchrow(query, question_id)

    async def mark_question_as_executed(self, question_id: int):
        query = "UPDATE bot_ask_lawyer SET execution = TRUE WHERE id = $1"
        await self.pool.execute(query, question_id)