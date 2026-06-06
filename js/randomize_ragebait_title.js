const ragebait_titles = [
  "When you delete the demo",
  "For those of us that are GPU poor",
  "When real engineers delete code",
  "When your AI strategy is a prompt",
  "When RAG is your a product"
];

function randomTitle() {
  const index = Math.floor(Math.random() * ragebait_titles.length);
  return ragebait_titles[index];
}

const title = randomTitle();

document.getElementById("ragebait-title").innerText = "\"" + title + "\"";