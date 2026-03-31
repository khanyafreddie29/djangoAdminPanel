from django.core.management.base import BaseCommand
import os
import glob


class Command(BaseCommand):
    help = 'Remove deprecated seed commands, keeping only seed_all_templates'

    def handle(self, *args, **kwargs):
        commands_dir = os.path.dirname(os.path.abspath(__file__))

        deprecated = [
            'seed_gig_templates.py',
            'seed_transaction_templates.py',
            'seed_dispute_templates.py',
            'seed_user_templates.py',
            'seed_gig_accepted_templates.py',
            'seed_gig_started_templates.py',
        ]

        deleted, skipped = 0, 0
        for filename in deprecated:
            filepath = os.path.join(commands_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                self.stdout.write(self.style.WARNING(f'Deleted: {filename}'))
                deleted += 1
            else:
                self.stdout.write(f'Not found (skipped): {filename}')
                skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! {deleted} files deleted, {skipped} not found.'
        ))