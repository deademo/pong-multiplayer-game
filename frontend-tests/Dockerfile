FROM node:22-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy test files
COPY . .

# Run tests by default
CMD ["npm", "test"]
