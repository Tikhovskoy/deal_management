document.addEventListener('DOMContentLoaded', function () {
    const mapElement = document.getElementById('map');
    if (!mapElement) {
        return;
    }

    const yandexApiKey = mapElement.dataset.apiKey;
    if (!yandexApiKey) {
        console.error('Yandex Maps API key is not provided.');
        return;
    }

    function loadYandexMaps() {
        const script = document.createElement('script');
        script.src = `https://api-maps.yandex.ru/2.1/?apikey=${yandexApiKey}&lang=ru_RU`;
        script.type = 'text/javascript';
        script.onload = () => ymaps.ready(initMap);
        document.head.appendChild(script);
    }

    function initMap() {
        const companiesData = mapElement.dataset.companies;
        const companies = JSON.parse(companiesData);

        const myMap = new ymaps.Map("map", {
            center: [55.76, 37.64],
            zoom: 10
        });

        if (companies.length === 0) {
            myMap.setCenter([55.76, 37.64], 5);
            return;
        }

        const myCollection = new ymaps.GeoObjectCollection();

        for (let i = 0; i < companies.length; i++) {
            const company = companies[i];
            const placemark = new ymaps.Placemark([company.lat, company.lon], {
                balloonContentHeader: company.title,
                balloonContentBody: company.address,
                hintContent: company.title
            });
            myCollection.add(placemark);
        }

        myMap.geoObjects.add(myCollection);

        myMap.setBounds(myCollection.getBounds(), {
            checkZoomRange: true,
            zoomMargin: 35
        });
    }

    loadYandexMaps();
});
