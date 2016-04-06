'use strict';

angular.module('predictrApp', ['ngRoute', 'pascalprecht.translate', 'ngCookies', 'ngResource', 'angular-ladda', 'ngAnimate', 'toastr'])
  .run(function($rootScope, $route, $translate, ServerInfo, Account) {
    // Initialize root scope
    $rootScope.$route = $route;
    $rootScope.serverInfo = ServerInfo.get();
    $rootScope.account = Account.get();
    $rootScope.changeLanguage = function(language) {
      $translate.use(language);
    };
  })
  .config(function($translateProvider, toastrConfig) {

    // I18n
    $translateProvider
      .useStaticFilesLoader({
        prefix: 'values/strings-',
        suffix: '.json'
      })
      .preferredLanguage('de')
      .useCookieStorage()
      .useSanitizeValueStrategy('escapeParameters');

    //Toastr
    angular.extend(toastrConfig, {
      allowHtml: true,
      timeOut: 3000,
      preventOpenDuplicates: true,

    });
  });
