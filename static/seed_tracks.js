
$('.add-track').click(addTrack)

async function addTrack() {
    const id = $(this).data('id')
    await axios.get(`/add_seed_track/${id}`)




}

$('#tempo').click(function () {
    alert('add songs with a similar number')


})

$('#key').click(function () {
    alert('add songs with a similar number')


})

const removeButtons = document.querySelectorAll('.add-track');

for (let btn of removeButtons) {
    btn.addEventListener('click', function (e) {
        e.target.remove();
        alert('added!')
    });



}



