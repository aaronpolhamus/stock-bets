# pull official base image
FROM node:13.12.0-alpine

# set working directory
WORKDIR /home/frontend

# add `/app/node_modules/.bin` to $PATH
ENV PATH /home/frontend/node_modules/.bin:$PATH

# install app dependencies
COPY ./frontend/package.json /home/frontend
COPY ./frontend/package-lock.json /home/frontend
RUN npm install
RUN npm install react-scripts@3.4.1 -g

# add app
COPY ./frontend /home/frontend

# start app
CMD ["npm", "start"]
