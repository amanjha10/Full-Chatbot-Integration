import json
import os
import uuid
from django.core.management.base import BaseCommand
from chatbot.models import RAGDocument


class Command(BaseCommand):
    help = 'Load FAQ data from JSON file into RAG documents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='refrence/data/documents/education_faq.json',
            help='Path to JSON file containing FAQ data'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing RAG documents before loading'
        )

    def handle(self, *args, **options):
        if options['clear']:
            deleted_count = RAGDocument.objects.count()
            RAGDocument.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f'Deleted {deleted_count} existing RAG documents')
            )

        file_path = options['file']
        if not os.path.exists(file_path):
            self.stderr.write(
                self.style.ERROR(f'File not found: {file_path}')
            )
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            documents_created = 0
            
            # Process general queries
            if 'general_queries' in data:
                for category, items in data['general_queries'].items():
                    documents_created += self._process_category_items(
                        items, f'general_queries.{category}', 'General Queries'
                    )
            
            # Process language requirements
            if 'language_requirements' in data:
                for category, items in data['language_requirements'].items():
                    documents_created += self._process_category_items(
                        items, f'language_requirements.{category}', 'Language Requirements'
                    )
            
            # Process scholarships
            if 'scholarships' in data:
                for category, items in data['scholarships'].items():
                    documents_created += self._process_category_items(
                        items, f'scholarships.{category}', 'Scholarships'
                    )
            
            # Process career prospects
            if 'career_prospects' in data:
                for category, items in data['career_prospects'].items():
                    documents_created += self._process_category_items(
                        items, f'career_prospects.{category}', 'Career Prospects'
                    )
            
            # Process firecrawl integrated data
            if 'firecrawl_integrated' in data:
                for category, items in data['firecrawl_integrated'].items():
                    documents_created += self._process_category_items(
                        items, f'firecrawl_integrated.{category}', 'Web Scraped Data'
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully loaded {documents_created} RAG documents')
            )
            
        except json.JSONDecodeError as e:
            self.stderr.write(
                self.style.ERROR(f'Invalid JSON file: {e}')
            )
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'Error loading data: {e}')
            )

    def _process_category_items(self, items, subcategory, main_category):
        """Process items from a specific category"""
        created_count = 0
        
        for item in items:
            if not isinstance(item, dict):
                continue
                
            question = item.get('question', '')
            answer = item.get('answer', '')
            
            if not question or not answer:
                continue
            
            # Extract metadata
            section = item.get('section', '')
            document = item.get('document', '')
            chunk_id = item.get('chunk_id', '')
            page = item.get('page', 0)
            
            # Determine priority based on category
            priority = self._get_priority(main_category, subcategory)
            
            # Create tags
            tags = [main_category, subcategory]
            if section:
                tags.append(section)
            if document:
                tags.append(document)
            
            # Create or update RAG document
            chunk_id_value = chunk_id if chunk_id else str(uuid.uuid4())
            rag_doc, created = RAGDocument.objects.get_or_create(
                chunk_id=chunk_id_value,
                defaults={
                    'question': question,
                    'answer': answer,
                    'section': section or main_category,
                    'document': document or 'FAQ Data',
                    'page': page,
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'Created: {question[:60]}...')
            else:
                # Update existing document
                rag_doc.question = question
                rag_doc.answer = answer
                rag_doc.section = section or main_category
                rag_doc.document = document or 'FAQ Data'
                rag_doc.page = page
                rag_doc.is_active = True
                rag_doc.save()
                self.stdout.write(f'Updated: {question[:60]}...')
        
        return created_count

    def _get_priority(self, main_category, subcategory):
        """Determine priority based on category"""
        high_priority_categories = [
            'general_queries.study_abroad_basics',
            'general_queries.visa_information',
            'scholarships.global_opportunities'
        ]
        
        medium_priority_categories = [
            'language_requirements',
            'career_prospects',
            'general_queries.accommodation'
        ]
        
        category_key = f'{main_category}.{subcategory}' if '.' not in main_category else subcategory
        
        if any(cat in category_key for cat in high_priority_categories):
            return 'high'
        elif any(cat in category_key for cat in medium_priority_categories):
            return 'medium'
        else:
            return 'low'
