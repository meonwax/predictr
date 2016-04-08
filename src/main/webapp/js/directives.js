'use strict';

angular.module('predictrApp')
  .directive('focusMe', function($timeout) {
    return {
      restrict: 'A',
      scope: {
        trigger: '@focusMe'
      },
      link: function(scope, element) {
        scope.$watch('trigger', function(value) {
          if (value === 'true') {
            $timeout(function() {
              element[0].focus();
            });
          }
        });
      }
    };
  })
  .directive('mybet', function() {
    return {
      restrict: 'A',
      require: 'ngModel',
      link: function(scope, element, attrs, ngModel) {

        function formatter(value) {
          if (value) {
            return value.scoreHome + ':' + value.scoreAway;
          }
        }
        ngModel.$formatters.push(formatter);

        function parser(value) {
          if (value) {
            var arr = value.split(':');
            if (arr.length == 2 && arr[0] && arr[1]) {
              var bet = {};
              bet.scoreHome = arr[0];
              bet.scoreAway = arr[1];
              return bet;
            }
          }
        }
        ngModel.$parsers.push(parser);
      }
    };
  });
