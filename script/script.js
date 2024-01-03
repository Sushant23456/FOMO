document.addEventListener('DOMContentLoaded', function() {
    var croppie = null;
    var fileInput = document.getElementById('file');
    var croppieContainer = document.getElementById('croppie-container');
    var uploadForm = document.getElementById('upload-form');
    var imageCropped = document.getElementById('image-cropped');

    fileInput.addEventListener('change', function(event) {
        var reader = new FileReader();
        reader.onload = function(e) {
            croppieContainer.style.display = 'block';
            croppie = new Croppie(document.getElementById('croppie'), {
                url: e.target.result,
                viewport: { width: 1080, height: 566 }, // Adjust as needed
                boundary: { width: 1200, height: 600 },
                showZoomer: true,
                enableResize: true,
                enableOrientation: true
            });
        };
        reader.readAsDataURL(this.files[0]);
    });

    document.getElementById('crop-image').addEventListener('click', function() {
        croppie.result({
            type: 'canvas',
            size: 'viewport'
        }).then(function(img) {
            imageCropped.value = img;
            croppieContainer.style.display = 'none';
            uploadForm.style.display = 'block';
        });
    });
});