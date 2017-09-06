var mwd_api_key = "c021ec02-2d18-4e7d-8507-4f940f531e77";

function getDefinition(word) {
    fetch(`http://www.dictionaryapi.com/api/v1/references/collegiate/xml/${word}?key=${mwd_api_key}`)
      .then(response => response.text())
      .then(data => console.log(data))
      .catch(error => console.error(error));
}