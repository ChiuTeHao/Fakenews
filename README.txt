All usage of 'url_detection' is commented out in 'server.py'. If the dependency problem is solved, they can be uncommented. I know of three ways to resolve the problem with 'datrie'.

1. Use early python 3.6; something like python 3.6.2.
2. Use conda. Conda has binary wheel of datrie for the latest python, version 3.7.
3. Compile datrie from source.

The full list of python dependencies is as follows.
tornado, pandas, python-docx, nltk, requests, datrie

Nodejs is no longer a dependency. Everything regarding nodejs and chromium are handled by docker.

Suppose one is already in the current directory.
The docker image can be built with 'docker build -t pup .'.
The nodejs server must be run with 'docker run -p 6175:6175 -v "$(pwd)"/img:/home/pup/img:ro -d pup'. It only listens to localhost.
The python server is then run with 'python server.py', and it utilizes port 6174. Change the ip in the source code to match one's need. It listens to localhost by default.
