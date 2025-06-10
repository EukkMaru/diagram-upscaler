const fs = require('fs');
data = JSON.parse(fs.readFileSync('./filtered_papers.json', 'utf8'));

let count = 0;

Object.keys(data).forEach((key) => {
    count++;
});
console.log(`Total number of papers: ${count}`);