# TRIVIA TIME

#### Languages Used: HTML, CSS, JS, PYTHON, FLASK & JINJA

#### Video Demo:  <URL HERE>
#### Description: Trivia Time is a simple CRUD web app that allows you to play and create trivias, you can create trivias not only for yourself and friends to play, but for the trivia that you created can be shared to everyone within the public trivias page. 

#### Before we talk about the project, I have to mention the fact that you can log in on this websites which will have it's own benefits due to the fact some features/pages on this website are only accessible if logged in.
#### due to the fact that: If you're not logged IN, 1. the page will not be accessible 2. our database wouldn't be able to remember you anyway

### There are 5 main pages:

#### -- Play (LOGIN NOT REQUIRED)
#### -- Create (LOGIN REQUIRED)
#### -- Public Trivias (LOGIN NOT REQUIRED)
#### -- Created Trivias (LOGIN REQUIRED)
#### -- Played Trivias (LOGIN REQUIRED)




### Play:

#### When entering the play page, there are 4 options (question category, number of questions, difficulty, question's type) you can either choose the options you want or leave them blank (except the amount of questions), then after pressing submit, the trivia will be generated for you,

#### it is generated through using an api from a website called "opentdb.com". when leaving (a) category/categories blank. a trivia with any of that specific option will be generated, e.g. if the difficulty category is left blank the trivia will generate questions with any difficulty within the trivia.

#### after having the trivia generated to you, you will be presented with the amount of questions you have entered in, after answering each question, you can click submit and your score will be shown to you aswell as each answer you got right and each answer you got wrong.

### Create:

#### Similar to the play page, you are presented with 4 options (question category, number of questions, difficulty, question's type) leaving a category as it's default value / blank will allow you to choose any category for each of your questions within the trivia you are creating.

#### after selecting your categories and number of questions, you will be brought to a page where you can enter the values for each of the questions and there will be a toggle near the top of the page asking whether you want your created trivia to be private (only seen by you) or public.

### Public Trivia:

#### This is where whether you toggled the visibility to public or private matters because any trivia's visibility that is set to public, will be displayed on this page allowing other people to play the trivia you have created and vice versa. 

### Created Trivias: 

#### Here will be shown every trivia you have created and allows you to replay them aswell, there is a button next to each trivia allowing you to switch the visibility to public or private, just incase you have a change of mind or made a mistake when setting the visibility

### Played Trivias:

#### this will be your history page of the trivias you have played, e.g. if you played trivia1 then trivia2, both trivia2 and trivia1 will be shown, if you played trivia1 twice in a row, trivia1 will appear twice in a row.

