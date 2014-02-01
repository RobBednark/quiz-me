# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'User'
        db.delete_table(u'questions_user')

        # Adding field 'Attempt.datetime_updated'
        db.add_column(u'questions_attempt', 'datetime_updated',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2014, 2, 1, 0, 0), auto_now=True, blank=True),
                      keep_default=False)


        # Changing field 'Attempt.user'
        db.alter_column(u'questions_attempt', 'user_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['user_.User'], null=True))
        # Adding field 'Answer.user'
        db.add_column(u'questions_answer', 'user',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['user_.User'], null=True),
                      keep_default=False)

        # Adding field 'Tag.datetime_added'
        db.add_column(u'questions_tag', 'datetime_added',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2014, 2, 1, 0, 0), auto_now_add=True, blank=True),
                      keep_default=False)

        # Adding field 'Tag.datetime_updated'
        db.add_column(u'questions_tag', 'datetime_updated',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2014, 2, 1, 0, 0), auto_now=True, blank=True),
                      keep_default=False)

        # Adding field 'Tag.user'
        db.add_column(u'questions_tag', 'user',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['user_.User'], null=True),
                      keep_default=False)

        # Adding field 'Question.user'
        db.add_column(u'questions_question', 'user',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['user_.User'], null=True),
                      keep_default=False)

        # Adding field 'Hint.datetime_added'
        db.add_column(u'questions_hint', 'datetime_added',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2014, 2, 1, 0, 0), auto_now_add=True, blank=True),
                      keep_default=False)

        # Adding field 'Hint.datetime_updated'
        db.add_column(u'questions_hint', 'datetime_updated',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2014, 2, 1, 0, 0), auto_now=True, blank=True),
                      keep_default=False)

        # Adding field 'Hint.user'
        db.add_column(u'questions_hint', 'user',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['user_.User'], null=True),
                      keep_default=False)

        # Adding field 'Quiz.datetime_added'
        db.add_column(u'questions_quiz', 'datetime_added',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2014, 2, 1, 0, 0), auto_now_add=True, blank=True),
                      keep_default=False)

        # Adding field 'Quiz.datetime_updated'
        db.add_column(u'questions_quiz', 'datetime_updated',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2014, 2, 1, 0, 0), auto_now=True, blank=True),
                      keep_default=False)

        # Adding field 'Quiz.user'
        db.add_column(u'questions_quiz', 'user',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['user_.User'], null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Adding model 'User'
        db.create_table(u'questions_user', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'questions', ['User'])

        # Deleting field 'Attempt.datetime_updated'
        db.delete_column(u'questions_attempt', 'datetime_updated')


        # Changing field 'Attempt.user'
        db.alter_column(u'questions_attempt', 'user_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['questions.User'], null=True))
        # Deleting field 'Answer.user'
        db.delete_column(u'questions_answer', 'user_id')

        # Deleting field 'Tag.datetime_added'
        db.delete_column(u'questions_tag', 'datetime_added')

        # Deleting field 'Tag.datetime_updated'
        db.delete_column(u'questions_tag', 'datetime_updated')

        # Deleting field 'Tag.user'
        db.delete_column(u'questions_tag', 'user_id')

        # Deleting field 'Question.user'
        db.delete_column(u'questions_question', 'user_id')

        # Deleting field 'Hint.datetime_added'
        db.delete_column(u'questions_hint', 'datetime_added')

        # Deleting field 'Hint.datetime_updated'
        db.delete_column(u'questions_hint', 'datetime_updated')

        # Deleting field 'Hint.user'
        db.delete_column(u'questions_hint', 'user_id')

        # Deleting field 'Quiz.datetime_added'
        db.delete_column(u'questions_quiz', 'datetime_added')

        # Deleting field 'Quiz.datetime_updated'
        db.delete_column(u'questions_quiz', 'datetime_updated')

        # Deleting field 'Quiz.user'
        db.delete_column(u'questions_quiz', 'user_id')


    models = {
        u'questions.answer': {
            'Meta': {'object_name': 'Answer'},
            'answer': ('django.db.models.fields.TextField', [], {}),
            'datetime_added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 2, 1, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            'datetime_updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 2, 1, 0, 0)', 'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['user_.User']", 'null': 'True'})
        },
        u'questions.attempt': {
            'Meta': {'object_name': 'Attempt'},
            'attempt': ('django.db.models.fields.TextField', [], {}),
            'correct': ('django.db.models.fields.BooleanField', [], {}),
            'datetime_added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 2, 1, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            'datetime_updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 2, 1, 0, 0)', 'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['questions.Question']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['user_.User']", 'null': 'True'})
        },
        u'questions.hint': {
            'Meta': {'object_name': 'Hint'},
            'answer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['questions.Answer']", 'null': 'True'}),
            'datetime_added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 2, 1, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            'datetime_updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 2, 1, 0, 0)', 'auto_now': 'True', 'blank': 'True'}),
            'hint': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['user_.User']", 'null': 'True'})
        },
        u'questions.question': {
            'Meta': {'object_name': 'Question'},
            'answer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['questions.Answer']", 'null': 'True'}),
            'datetime_added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 2, 1, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            'datetime_updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 2, 1, 0, 0)', 'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.TextField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['user_.User']", 'null': 'True'})
        },
        u'questions.quiz': {
            'Meta': {'object_name': 'Quiz'},
            'datetime_added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 2, 1, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            'datetime_updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 2, 1, 0, 0)', 'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['user_.User']", 'null': 'True'})
        },
        u'questions.tag': {
            'Meta': {'object_name': 'Tag'},
            'datetime_added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 2, 1, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            'datetime_updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 2, 1, 0, 0)', 'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['user_.User']", 'null': 'True'})
        },
        u'user_.user': {
            'Meta': {'object_name': 'User'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_admin': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        }
    }

    complete_apps = ['questions']