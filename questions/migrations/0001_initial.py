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
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['emailusername.User'], null=True)),
            ('question', self.gf('django.db.models.fields.TextField')()),
            ('answer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['questions.Answer'], null=True)),
        ))
        db.send_create_signal(u'questions', ['Question'])

        # Adding model 'Answer'
        db.create_table(u'questions_answer', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('datetime_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('datetime_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['emailusername.User'], null=True)),
            ('answer', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'questions', ['Answer'])

        # Adding model 'Attempt'
        db.create_table(u'questions_attempt', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('datetime_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('datetime_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['emailusername.User'], null=True)),
            ('attempt', self.gf('django.db.models.fields.TextField')()),
            ('correct', self.gf('django.db.models.fields.BooleanField')()),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['questions.Question'])),
        ))
        db.send_create_signal(u'questions', ['Attempt'])

        # Adding model 'Hint'
        db.create_table(u'questions_hint', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('datetime_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('datetime_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['emailusername.User'], null=True)),
            ('answer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['questions.Answer'], null=True)),
            ('hint', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'questions', ['Hint'])

        # Adding model 'Tag'
        db.create_table(u'questions_tag', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('datetime_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('datetime_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['emailusername.User'], null=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=1000)),
        ))
        db.send_create_signal(u'questions', ['Tag'])

        # Adding model 'Quiz'
        db.create_table(u'questions_quiz', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('datetime_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('datetime_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['emailusername.User'], null=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=1000)),
        ))
        db.send_create_signal(u'questions', ['Quiz'])

        # Adding model 'QuestionTag'
        db.create_table(u'questions_questiontag', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('datetime_added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('datetime_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['emailusername.User'], null=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['questions.Question'])),
            ('tag', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['questions.Tag'])),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'questions', ['QuestionTag'])

        # Adding model 'UserTag'
        db.create_table(u'questions_usertag', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['emailusername.User'])),
            ('tag', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['questions.Tag'])),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'questions', ['UserTag'])


    def backwards(self, orm):
        # Deleting model 'Question'
        db.delete_table(u'questions_question')

        # Deleting model 'Answer'
        db.delete_table(u'questions_answer')

        # Deleting model 'Attempt'
        db.delete_table(u'questions_attempt')

        # Deleting model 'Hint'
        db.delete_table(u'questions_hint')

        # Deleting model 'Tag'
        db.delete_table(u'questions_tag')

        # Deleting model 'Quiz'
        db.delete_table(u'questions_quiz')

        # Deleting model 'QuestionTag'
        db.delete_table(u'questions_questiontag')

        # Deleting model 'UserTag'
        db.delete_table(u'questions_usertag')


    models = {
        u'emailusername.user': {
            'Meta': {'object_name': 'User'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_admin': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'questions.answer': {
            'Meta': {'object_name': 'Answer'},
            'answer': ('django.db.models.fields.TextField', [], {}),
            'datetime_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'datetime_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['emailusername.User']", 'null': 'True'})
        },
        u'questions.attempt': {
            'Meta': {'object_name': 'Attempt'},
            'attempt': ('django.db.models.fields.TextField', [], {}),
            'correct': ('django.db.models.fields.BooleanField', [], {}),
            'datetime_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'datetime_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['questions.Question']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['emailusername.User']", 'null': 'True'})
        },
        u'questions.hint': {
            'Meta': {'object_name': 'Hint'},
            'answer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['questions.Answer']", 'null': 'True'}),
            'datetime_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'datetime_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'hint': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['emailusername.User']", 'null': 'True'})
        },
        u'questions.question': {
            'Meta': {'object_name': 'Question'},
            'answer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['questions.Answer']", 'null': 'True'}),
            'datetime_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'datetime_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.TextField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['emailusername.User']", 'null': 'True'})
        },
        u'questions.questiontag': {
            'Meta': {'object_name': 'QuestionTag'},
            'datetime_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'datetime_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['questions.Question']"}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['questions.Tag']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['emailusername.User']", 'null': 'True'})
        },
        u'questions.quiz': {
            'Meta': {'object_name': 'Quiz'},
            'datetime_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'datetime_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['emailusername.User']", 'null': 'True'})
        },
        u'questions.tag': {
            'Meta': {'object_name': 'Tag'},
            'datetime_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'datetime_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'questions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['questions.Question']", 'null': 'True', 'through': u"orm['questions.QuestionTag']", 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['emailusername.User']", 'null': 'True'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'users'", 'to': u"orm['emailusername.User']", 'through': u"orm['questions.UserTag']", 'blank': 'True', 'symmetrical': 'False', 'null': 'True'})
        },
        u'questions.usertag': {
            'Meta': {'object_name': 'UserTag'},
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['questions.Tag']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['emailusername.User']"})
        }
    }

    complete_apps = ['questions']