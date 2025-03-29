from sqlalchemy import create_engine
from datetime import datetime
import logging
from data_handler import fee_details_table, engine

logging.basicConfig(level=logging.ERROR)

class FeeDetail:
    @staticmethod
    def add_fee_detail(fee_detail):
        conn = engine.connect()
        trans = conn.begin()
        try:
            conn.execute(fee_details_table.insert(), fee_detail)
            trans.commit()
        except Exception as e:
            print(f"Error adding fee detail: {e}")
            trans.rollback()
        finally:
            conn.close()

    @staticmethod
    def get_latest_fee_detail_by_member_id(member_id):
        """
        Fetch the latest fee detail for a given member.
        """
        conn = engine.connect()
        try:
            result = conn.execute(
                fee_details_table.select()
                .where(fee_details_table.c.member_id == member_id)
                .order_by(fee_details_table.c.due_date.desc())
                .limit(1)
            ).fetchone()
            return dict(result._mapping) if result else None
        finally:
            conn.close()

    @staticmethod
    def get_all_fee_details(filter_due_date=None, filter_name=None, filter_room_number=None,
                            filter_amount_paid_status=None, filter_advance_paid_status=None,
                            limit=None, offset=None):
        with engine.connect() as conn:
            query = fee_details_table.select()
    
            # Apply filters
            if filter_due_date:
                query = query.where(fee_details_table.c.due_date <= filter_due_date)
            if filter_name:
                query = query.where(fee_details_table.c.name.ilike(f"%{filter_name}%"))
            if filter_room_number:
                query = query.where(fee_details_table.c.room_number == filter_room_number)
            if filter_amount_paid_status:
                query = query.where(fee_details_table.c.fee_paid_status == filter_amount_paid_status)
            if filter_advance_paid_status:
                query = query.where(fee_details_table.c.advance_paid_status == filter_advance_paid_status)
    
            # Add pagination
            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)
    
            # Execute query and fetch results
            results = conn.execute(query).fetchall()
            return [dict(row._mapping) for row in results]

    @staticmethod
    def get_fee_detail_by_id(fee_id):
        conn = engine.connect()
        try:
            result = conn.execute(fee_details_table.select().where(fee_details_table.c.fee_id == fee_id)).fetchone()
            return dict(result._mapping) if result else None
        finally:
            conn.close()

    @staticmethod
    def update_fee_detail(fee_id, updated_data):
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                conn.execute(fee_details_table.update().where(fee_details_table.c.fee_id == fee_id).values(updated_data))
                trans.commit()
            except Exception as e:
                logging.error(f"Error updating fee detail: {e}")
                trans.rollback()
    
    @staticmethod
    def get_members_with_unpaid_fees():
        """
        Fetch members who have not paid their fees before the due date.
        """
        with engine.connect() as conn:
            query = fee_details_table.select().where(
                (fee_details_table.c.fee_paid_status == 'N') &
                (fee_details_table.c.due_date < datetime.now())
            )
            results = conn.execute(query).fetchall()
            return [dict(row._mapping) for row in results]