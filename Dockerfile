# leverage the renci python base image
FROM renciorg/renci-python-image:v0.0.1

# set up working directory
RUN mkdir /home/nru
WORKDIR /home/nru

# make sure all is writeable for the nru USER later on
RUN chmod -R 777 .

# install python package requirements
ADD ./requirements.txt /home/nru/requirements.txt
RUN pip install -r /home/nru/requirements.txt --src /usr/local/src

# switch to the non-root user (nru). defined in the base image
USER nru

# install code
ADD ./bl_lookup /home/nru/bl_lookup
ADD ./main.py /home/nru/main.py
ADD ./setup.py /home/nru/setup.py

EXPOSE 8144

# define the startup entrypoint
ENTRYPOINT ["python", "main.py"]
