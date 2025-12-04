
const axios = require('axios');
const fs = require('fs').promises;

async function transformUrls() {
  try {
    const response = await axios.get("https://raw.githubusercontent.com/drmlive/fancode-live-events/refs/heads/main/fancode.json");
    let data = response.data;

    if (data.matches && Array.isArray(data.matches)) {
      data.matches.forEach(match => {
        if (match.adfree_url && typeof match.adfree_url === 'string' && match.adfree_url.startsWith("https://in-mc-fdlive.fancode.com/")) {
          match.adfree_url = match.adfree_url.replace("https://in-mc-fdlive.fancode.com/", "https://bd-mc-fdlive.fancode.com/");
        }
      });
    }

    await fs.writeFile("fancodebd_by_siam.json", JSON.stringify(data, null, 4));
    console.log("Transformation complete. Check fancodebd_by_siam.json");

  } catch (error) {
    console.error("Error:", error.message);
  }
}

transformUrls();
