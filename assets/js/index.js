import Swal from 'sweetalert2'
import './sweetalert.js'
import './htmx-additional.js'
import ApexCharts from 'apexcharts'

import '../css/index.css'
import '../css/app.css'
import '../css/app-dark.css'
import 'bootstrap-icons/font/bootstrap-icons.css';
import 'sweetalert2/src/sweetalert2.scss'


const body = document.body;
const theme = localStorage.getItem('theme')

if (theme)
  document.documentElement.setAttribute('data-bs-theme', theme)

window.ApexCharts = ApexCharts;

document.addEventListener('DOMContentLoaded', function () {
  var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl)
  })
}, false);
