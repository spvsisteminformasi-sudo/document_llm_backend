import click
from flask.cli import with_appcontext
from app.models import db
from sqlalchemy import text
import os

@click.command('seed')
@with_appcontext
def seed_command():
    """Seed the database with initial data."""
    try:
        # Get the path to the seeds directory
        seeds_dir = os.path.join(os.path.dirname(__file__), '..', 'seeds')
        
        # Execute users.sql
        with open(os.path.join(seeds_dir, 'users.sql'), 'r') as f:
            sql = f.read()
            db.session.execute(text(sql))
            
        db.session.commit()
        click.echo('Database seeded successfully!')
        
    except Exception as e:
        click.echo(f'Error seeding database: {e}')
        db.session.rollback()
