## #TODO / #Backlog / #Features / #Stories
(NOTE: deprecate the Trello board and move the backlog items from https://trello.com/b/5WCzHwdo/quizme to here)

1. 10.24.20 ADD color-coding for # questions seen past day/week/... (maybe as static numbers, e.g., 1-5=red, 6-10=orange, ...; maybe as percentages of total for that tag, e.g., 100%=green, 80-99%-light green, ...)
1. 10.5.20 ADD show total number of questions per tag
1. 9.21.20 ADD feature to create a blank attempt for a question when it is added (Why?  To eliminate the problem of seeing unanswered questions first (or not seeing them if nulls are last)
1. 9.19.20 ADD hover over tags for question to show questions as a popup list for easier viewing
1. 9.19.20 ADD option for default opening hints and answers
1. 9.16.20 Admin: add question: show number of questions for each tag name in the dropdown to select a tag
1. 9.16.20 Admin: Tab list view: show number of questions for each tage
1. 9.14.20 scheduled (e.g., iterate through x selected tags one at a time, select y cards from each tag)
    * input: selected tags
    * input: x cards per tag
    * implementation: selected_tags_set, remaining_tags_set
    * implementation: instead of selected tags, choose one tag from remaining_tags_set, and use that as the selected tag (don't want to use all remaining tags, because we need to know which tag to remove from the set; or else remove one of the tags associated with the question that is in the remaining_tags_set)
    ** implementation: store the sets, so that when user selects that set of tags again, it uses the same set
1. 9.14.20 random time range (e.g., choose card from 1 day range from date of next card)
1. 9.13.20 ADD ability to type in question without saving it or having to delete it (practice typing; type it to learn it)
1. 9.5.20 ADD functionality to import from other sources (iBooks notes, Google Play Books notes, Evernote, Keep, Google Sheets, Notion, ...)
1. 8.16.20 CHANGE: Django Admin - prepopulate user with the logged-in user  (see https://stackoverflow.com/questions/53253288/django-admin-prepopulate-field-and-set-readonly)
1. 8.16.20 CHANGE Django Admin -- autopopulate the user when adding a new question/answer/tag
1. 8.16.20 CHANGE see if Django admin can be set to not prepulate dropdowns (e.g., viewing a tag, don't populate the question dropdowns; when adding a question, don't populate the answer dropdowns)
1. 8.14.20 NEW modify so that in multi-user environment, /flashcard only sees logged-in user's tags and questions; admin: user cannot see/edit other users content
1. 8.14.20 NEW capture HTTP requests/responses in different db (endpoint, IP address, status code) (e.g., django-wiretap) (WHY? to capture suspicious activity)
1. 8.14.20 NEW add feature to show a random photo from some collection (e.g., Google Photos, unsplash, r/pics)
1. 8.13.20 NEW optionally show questions based questions matching text inputted by user
1. 8.12.20 CHANGE combine questions and answers in the same table; I made them separate, thinking it would be useful to have multiple questions for the same answer, but I don't think that is worth it anymore; (why? so it is simpler to add and edit questions and answers in a single page)
1. 8.11.20 NEW add a section to show all answers/attempts submitted for a given question
1. 8.08.20 NEW add option to cycle through random fonts for each question
1. 8.06.20 NEW quiz on questions with no tags
1. 8.01.20 NEW Add auto-advance option for playing audios/videos automatically, and auto-advancing to the next one (why?  to listen to flashcards while walking, running, ...)
1. 8.01.20 NEW Add a "seen" button, or else consider seen if no atttempt or schedule;
  Use cases:
    - create a schedule
    - mark only percent correct
    - mark only percent confidence
    - mark both percent correct and percent confidence

    |attempt_text  |schedule  |%_correct  |%_confidence   |outcome|
    |------------  |--------  |---------  |------------   |-------|
    |yes           |yes       |yes        |yes            |typical schedule|
    |no            |no        |no         |no             |mark seen (stats are null, so ignore when querying based on %correct/confidence)|
    |no            |no        |yes        |yes            |mark seen and capture stats|  
1. 7.31.20 CHANGE get nicer UI colors and font (e.g., https://www.mentalnodes.com/a-gardening-guide-for-your-mind)
1. 7.30.20 NEW add input for % percent confidence in answer (and then optionally use that for picking next question)
1. 7.28.20 COMMENT add to the Readme a list of features, particularly the ones that make this different from other apps
1. 7.27.20 NEW admin: add related schedules to questions, but make them read-only (why? to see what schedules are associated with a question, so I don't have to create a db query to see them)
1. 7.27.20 NEW show/view stats of cards reviewed/seen and cards added each day, week, month, year for the past n months  (#high)  
  query: foreach tag:
    - return all schedules for that tag, DESC by date_added
      (last schedule for each question, or all schedules?)
1. 7.15.20 PERFORMANCE check if there is an unnecessary redirect; when hitting http://127.0.0.1:8000/question/ there is a ("GET / HTTP/1.1" 302 0) and _get_next_question() logs the same messages twice
1. 7.18.20 NEW Get running on linode
1. 7.24.20 NEW add a button to deselect/clear all tags
1. 7.24.20 NEW get next question randomly; e.g., for the selected tags, store the last question seen in random mode, and get a random question from everything older than that scheduled/last seen, so that all questions are being cycle through before being seen again; if doing SQL random SELECT, consider:  
https://stackoverflow.com/questions/8674718/best-way-to-select-random-rows-postgresql  
https://stackoverflow.com/questions/962619/how-to-pull-a-random-record-using-djangos-orm  
https://stackoverflow.com/questions/22816704/django-get-a-random-object  
https://books.agiliq.com/projects/django-orm-cookbook/en/latest/random.html
1. 7.23.20 NEW consider using different markdown packages, e.g.,  
https://github.com/agusmakmun/django-markdown-editor  
https://github.com/neutronX/django-markdownx  
https://github.com/erwinmatijsen/django-markdownify  
https://github.com/sv0/django-markdown-app
1. 7.15.20 ADD a RELEASE HISTORY / CHANGE LOG page to see what's been changed when
1. 7.17.20 FIX django-pagedown not working with Debug=False (add question: not showing markdown; command+k not working)
1. 7.20.20 PERFORMANCE speed up admin Tags page; see https://stackoverflow.com/questions/52386873/django-admin-slow-using-tabularinline-with-many-to-many-field
1. 7.15.20 TEST change tests to use pytest (consider pytest-django)
1. 7.15.20 ADD code coverage (maybe after changing to pytest) (consider pytest-cov)
1. 7.15.20 TEST add tests for many questions/answers/tags/schedules using factory-boy

1. 7.16.20 FIX why markdown displayed for answer in question page is displayed differently from the answer page, e.g., 
    > \> one  
    > two  

    shows as two lines in the question page, but one line on the answer page (no linefeeds)
1. 7.12.20 DEV_PROCESS update the release process to use github "releases" (why? to see release history, and see what was added when) (e.g., https://github.com/timmyomahony/django-pagedown/releases) (start with 0.10.0?)
1. 6/24/20 FEATURE: when outputting dates, add the day-of-the-week, e.g. *__Tue__ June 23, 2020, 3:42 a.m.*
1. 7.15.20 ADD example fixture data (a user, some questions, answers, tags)
1. 7.14.20 REFACTOR See if emailusername can be eliminated
1. 7/4/20, 3/28/15 allow a tree structure of tags, so that selecting a tag would select that and everything below it [suggested by Nev] (I discovered that I'm not reviewing as many flashcards because of not having this; e.g., select all non-software tags)
1. 7.12.20 FEATURE consider a "frequency" field to indicate how often to see the flashcard (why? to show important/frequent cards that I want to see often, like daily, before other cards that are waiting to be seen before now) (e.g., show this card every 1 days, and if it hasn't been seen in the last day, then show it before other cards) #high  

    * from last time seen, calc next due date (last_seen + frequency_interval)
    * order by either due ascending, or percent_overdue (amount_overdue / frequency_interval)
1. 7.12.20 UPGRADE Upgrade splinter to the latest, using headless Chrome and/or Firefox instead of phantomjs
1. 7.15.20 ADD a separate select-tags page to be able to change tags without submitting an answer
1. 7.14.20 COMMENT README cleanup (get rid of Naming Ideas; check formatting; proofread whole file)
1. 7.12.20 BUG If there is no valid session, when going to /login/?next=/question/ , it gives a 404 error instead of going to the login screen (this seems to happen when switching between databases, I don't know why).  WORKAROUND: navigate to the /admin page, it will prompt for login, login, and then you can access the question page
1. 7.12.20 FEATURE prefill interval with values from previous schedule (why? to save time when reviewing)
1. 7.12.20 FEATURE order by interval secs (amount of time scheduled to be seen again) (why? to practice what I am actively learning)
1. 7/4/20 FEATURE: make question and answer editable while quizzing
1. 7/4/20 FEATURE: optionally sort tags by date added, or just show the date added
1. 6/24/20 FEATURE: add *time_since_last_seen* field to schedule, e.g., the amount of time (secs, and maybe human-readable, and maybe previous date seen) between this response and the last response
1. 6/24/20 FEATURE: show questions ordered by importance
1. 6/24/20 FEATURE: add favorite or "like" percentage value for responses; similar to importance, but more for enjoyment of the question; add option to show questions sorted by "like"
1. 9/14/16 STYLE: in list of tags, change the color of the tag if the tag is selected, to make it clear which are selected
1. 9/11/16 FEATURE: For the selected tags, show them one per line right under "Tags selected:", along with num_questions and time periods, as is shown in the next section with all the tags.  As a user, I want to see these tags at the top and not have to hunt for them.
1. 9/7/16 MODIFY: in the admin, modify it so that the width of the question/answer text isn't a single line and extremely wide
1. 9/5/16 FEATURE: save the duration/interval to attempt table in the database; then show this duration for the answer, so the user can determine how well they did for the actual interval compared to the desired interval; also, consider adding query criteria for a quiz to say "show me all questions with an interval of less than 2 days"
1. 9/5/16 FEATURE: for a quiz, make it possible to exclude questions with specified tags (e.g., quiz with all 'python' tags, except for questions that also contain the page 'web pages to review')
1. 9/5/16 TEST: add tests for:
    - num_questions (for each tag)
    - each interval:
        - -now
        - 10m-1h
        - 1h-1d
        - 1d-1w
        - 1w-1mo
        - 1mo-1y
        - unseen
1. 7/1/15 FEATURE: in addition to tags, consider keywords
1. 6/28/15 FEATURE: show how long (duration/interval) it has been between when we last answered the question and now; this will me when I answer determine how long I want to set the next interval (both question and answer pages)
1. 05/17/15 show the number of questions recently answered/scheduled (e.g., 0-10mins=[5]  10-30mins=[12] 30m-2h=[4]  0-2h=[21])  #high
1. 3/10/15 don't allow duplicate tags to be created
1. Export (export questions via csv / json / yaml / xml / python data structure / plain text).  Find a way to maintain referential integrity.
1. 01/23/15 Django Admin: add ability to edit answer in same page as editing question.
1. 2/11/15  Show the schedule numbers for the total of selected tags (just like is done for each individual tag)  #high
1. 12/31/14 Allow a quiz mode that consists of a set of questions, and the user can go back and change their answers as much as they want (e.g., as part of an interview)
1. 12/31/14 Make it possible to view questions that don't have any tags ("untagged")  #high
1. 12/31/14 Have a "review all" mode that goes through all questions for the selected tags, showing you number seen and number remaining.
1. 12/31/14 REFACTOR: change all datetime_* variables to either date_* or time_\*
1. 12/31/14 Change all timezones to UTC
1. 12/30/14 Implement variations (a question can have variations -- other questions that are similar but modified in a different way; e.g., 2+3=? could be a variation of 2+2=?); this is helpful so that you don't get in the habit of seeing the question and remembering the answer without understanding it
1. 12/27/14 ask how well the question was answered (maybe percentage; excellent / good / bad)
1. 12/21/14 Add contributors.md
1. 12/21/14 Add to readthedocs
1. 02/15/15 Consider adding a priority field (interval is ideally when you want to see it again, but priority is how important it is to you; so 2 different questions could have the same interval, but the one with the higher priority gets shown first; however, what to do if question1 has interval 1 month and priority "high", and question2 has interval 1 minute and priority "low" -- which gets shown first?)
1. 11/17/14 add ability to select all or deselect all for tags  #high
1. 10/20/14 add search ability, to search questions/answers for specified keywords
1. 10/20/14 in the admin, when viewing a question, show the answer as an inline that can also be edited; likewise, when viewing an answer, show the question inline  #high
1. 10/18/14 per Steven Jonas, have a way to find other questions (or bookmarked webpages) with similar content to help form associations and new insights
1. 10/18/14 have questions that are a single webpagge to review (a url), and show the content of the webpage instead of just a link
1. Show linefeeds as linefeeds for questions/answers/attempts (add <br/> tags; or add a rich text editor)
1. add an inline in the admin to edit the answer for a given question
1. ability to change tags for the question shown #high
1. 7/14/14 ADD a "SKIP" button to skip a question Why? Because user wants to go to the next card, but still wants the skipped card to be queued up.  "skip" means "show me the second card instead" or "push this card down in the stack to the second position" (How would that work?  Skipped for how long?  Where would it go in the queue? Can the user only skip a single card?)
1. 7/14/14 - capture the elapsed time that it took the user to reply
1. 7/14/14 - show all questions/answers for given tags on a single page
1. add documentation for other users to use
1. FEATURE: display url's as clickable url's (href's) if they aren't already in markdown url format #high
1. Import (import questions via csv / json / yaml / python data structure)
1. Questions (add questions from the web page instead of the admin)
1. consider allowing a hierarchy of tags, e.g.,
    - `** Programming`
    - `**** Languages`
    - `****** Python`
    - `****** Perl`
    - `****** C`
    - `** Methodologies`
    - `**** Agile`
    - (maybe allow multiple parent/child relationships)
1. NewUser registration
    * page to create account
    * email address verification/registration
1. Footer: 
    * show total number of questions
1. Review mode: just show questions and answers
1. email questions
1. Questions (modify questions from the web page while asking the question)
1. "Ignore" tag -- never see the question again
1. private questions/answers
1. Front-end:
    * ability to add questions/answers
    * ability to modify questions/answers on-the-fly
1. versions of questions/answers
