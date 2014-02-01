# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Question'
        db.create_table(u'questions_question', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('datetime_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('datetime_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('question', self.gf('django.db.models.fields.TextField')()),
            ('answer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['questions.Answer'], null=True)),
        ))
        db.send_create_signal(u'questions', ['Question'])

        # Adding model 'Answer'
        db.create_table(u'questions_answer', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('answer', self.gf('django.db.models.fields.TextField')()),
            ('datetime_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('datetime_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'questions', ['Answer'])

        # Adding model 'User'
        db.create_table(u'questions_user', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'questions', ['User'])

        # Adding model 'Attempt'
        db.create_table(u'questions_attempt', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('attempt', self.gf('django.db.models.fields.TextField')()),
            ('correct', self.gf('django.db.models.fields.BooleanField')()),
            ('datetime_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['questions.Question'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['questions.User'], null=True)),
        ))
        db.send_create_signal(u'questions', ['Attempt'])

        # Adding model 'Hint'
        db.create_table(u'questions_hint', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('answer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['questions.Answer'], null=True)),
            ('hint', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'questions', ['Hint'])

        # Adding model 'Tag'
        db.create_table(u'questions_tag', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=1000)),
        ))
        db.send_create_signal(u'questions', ['Tag'])

        # Adding model 'Quiz'
        db.create_table(u'questions_quiz', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=1000)),
        ))
        db.send_create_signal(u'questions', ['Quiz'])


    def backwards(self, orm):
        # Deleting model 'Question'
        db.delete_table(u'questions_question')

        # Deleting model 'Answer'
        db.delete_table(u'questions_answer')

        # Deleting model 'User'
        db.delete_table(u'questions_user')

        # Deleting model 'Attempt'
        db.delete_table(u'questions_attempt')

        # Deleting model 'Hint'
        db.delete_table(u'questions_hint')

        # Deleting model 'Tag'
        db.delete_table(u'questions_tag')

        # Deleting model 'Quiz'
        db.delete_table(u'questions_quiz')


    models = {
        u'questions.answer': {
            'Meta': {'object_name': 'Answer'},
            'answer': ('django.db.models.fields.TextField', [], {}),
            'datetime_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'datetime_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'questions.attempt': {
            'Meta': {'object_name': 'Attempt'},
            'attempt': ('django.db.models.fields.TextField', [], {}),
            'correct': ('django.db.models.fields.BooleanField', [], {}),
            'datetime_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['questions.Question']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['questions.User']", 'null': 'True'})
        },
        u'questions.hint': {
            'Meta': {'object_name': 'Hint'},
            'answer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['questions.Answer']", 'null': 'True'}),
            'hint': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'questions.question': {
            'Meta': {'object_name': 'Question'},
            'answer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['questions.Answer']", 'null': 'True'}),
            'datetime_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'datetime_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.TextField', [], {})
        },
        u'questions.quiz': {
            'Meta': {'object_name': 'Quiz'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1000'})
        },
        u'questions.tag': {
            'Meta': {'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1000'})
        },
        u'questions.user': {
            'Meta': {'object_name': 'User'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['questions']