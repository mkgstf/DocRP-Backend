from app import db
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app
import logging

logger = logging.getLogger(__name__)

def commit_changes():
    """
    Helper function to commit changes to the database with error handling
    """
    try:
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error: {str(e)}")
        return False

def add_to_db(obj):
    """
    Helper function to add an object to the database
    """
    try:
        db.session.add(obj)
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error adding to database: {str(e)}")
        return False

def delete_from_db(obj):
    """
    Helper function to delete an object from the database
    """
    try:
        db.session.delete(obj)
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error deleting from database: {str(e)}")
        return False

def get_paginated_results(query, page, per_page=None):
    """
    Helper function to get paginated results from a query
    """
    if per_page is None:
        per_page = current_app.config.get('ITEMS_PER_PAGE', 20)
    
    return query.paginate(page=page, per_page=per_page, error_out=False)