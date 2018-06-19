'use strict';

angular.module('predictrApp')
  .controller('RulesCtrl', function($rootScope, $scope, $sce, $interpolate, rules) {
    var html = marked(rules);
    $scope.content = $sce.trustAsHtml($interpolate(html)($rootScope.serverInfo));
    $rootScope.loading = false;
  });
