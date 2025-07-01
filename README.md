**Summary**  
Our project is built using django for the backend and strictly  HTML/ Taiwind-CSS for the frontend.
**Structure of our project**       
**Django ProjectName**: Poliagent   
**Django Appname**: PoliagentX    
**Tailwind appname**: theme

**Setup**  
1.**Creating a virtual environment**  
It is advisable to have a virtual environment for the project. NB: Make sure python is installed (preferably version 3.10 or later).
Assuming the virtual environment name is venv:

**Linux:**  
Navigate to the folder where the application is to be run from.
Install pip sudo apt-get install python3-pip.
Install the virtual environment sudo pip3 install virtualenv.
Create the virtual environment virtualenv venv.
Activate the virtual environment source venv/bin/activate. To deactivate the virtual environment deactivate.

**Windows:**   

1.**Using WSL**   
Set up WSL (Windows Subsystem for Linux) in order to take full advantage of all the functionality of virtual environments on Windows 10. This allows the running of a full Linux distribution within Windows.
Proceed to follow the steps outlined for Linux above to set up a virtual environment.  

2.**Without WSL**   
Navigate to the folder where the application is to be run from.
Install the virtual environment pip install virtualenv.
Create the virtual environment virtualenv venv.
Activate the virtual environment venv\Scripts\activate. To deactivate the virtual environment deactivate. 

**2. Cloning the project**   
Navigate into the project's directory
Clone the project git clone <PROJECT_GIT_URL>
Make sure the virtual environment is activated
Run pip install -r requirements.txt to install all the required dependencies. They are listed in the requirements.txt file found in the root folder of the project.  

3.**Running the django app**            
Assuming the app runs on port 8000, 

**One-time running**   
**To run the application**

Navigate to the project's directory in the terminal.
Run the following command: python manage.py runserver. Please note that if you are using a python version that requires you to use python3, then use python3 manage.py runserver
Open a browser and go the following link: http://127.0.0.1:8000.
It is advisable to have a virtual environment for the project. NB: Make sure python is installed (preferably version 3.10 or later).
Assuming the virtual environment name is venv:

**Linux:**  
Navigate to the folder where the application is to be run from.
Install pip sudo apt-get install python3-pip.
Install the virtual environment sudo pip3 install virtualenv.
Create the virtual environment virtualenv venv.
Activate the virtual environment source venv/bin/activate. To deactivate the virtual environment deactivate.

**Windows:**  
1.**Using WSL**  
Set up WSL (Windows Subsystem for Linux) in order to take full advantage of all the functionality of virtual environments on Windows 10. This allows the running of a full Linux distribution within Windows.
Proceed to follow the steps outlined for Linux above to set up a virtual environment.

2.**Without WSL**    
Navigate to the folder where the application is to be run from.
Install the virtual environment pip install virtualenv.
Create the virtual environment virtualenv venv.
Activate the virtual environment venv\Scripts\activate. To deactivate the virtual environment deactivate.

**Starting taiwind development server**   
Run the command: python manage.py tailwind start   
NB:This command compiles your inline tailwind css styles(utility classes) on the the styles.css.

**Adding & editing django templates(Html files)**     
Add you html files in the PoliagentX templates directory
Remember to extend the base.html file for inheritance of common features({% extend base.html %}.
Embedd your html content in betwen {% block content %} & {% endblock %}. Where this will automatically add your content intpo the <main></main> block in the base.html   
NB:Your content must only contain the neccesary layout/html tags.Some tags are already in the base.html i.e <html>,<body>,<head> are inherited from the base.html hence don't include them in your content.      
**NB:take advantage of the tailwind cheat sheat**

  




