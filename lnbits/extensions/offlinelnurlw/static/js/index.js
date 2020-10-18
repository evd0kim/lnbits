/* global Vue, VueQrcode, _, Quasar, LOCALE, windowMixin, LNbits */

Vue.component(VueQrcode.name, VueQrcode)

var locationPath = [
  window.location.protocol,
  '//',
  window.location.host,
  window.location.pathname
].join('')

var mapWithdrawLink = function (obj) {
  obj._data = _.clone(obj)
  obj.date = Quasar.utils.date.formatDate(
    new Date(obj.time * 1000),
    'YYYY-MM-DD HH:mm')
  return obj
}

new Vue({
  el: '#vue',
  mixins: [windowMixin],
  data: function () {
    return {
      format: 'po',
      checker: null,
      withdrawLinks: [],
      withdrawLinksTable: {
        columns: [
          {name: 'title', align: 'left', label: 'Title', field: 'title'},
          {name: 'id', align: 'left', label: 'ID', field: 'id'},
          {name: 'private_key', align: 'left', label: 'Key', field: 'private_key'},
          {
            name: 'amount',
            align: 'right',
            label: 'Amount withdrawn',
            field: 'amount'
          },
        ],
        pagination: {
          rowsPerPage: 10
        }
      },
      formDialog: {
        show: false,
        secondMultiplier: 'seconds',
        secondMultiplierOptions: ['seconds', 'minutes', 'hours'],
        data: {
          is_unique: false
        }
      },
      simpleformDialog: {
        show: false,
        data: {
          is_unique: false,
          title: 'ATM link',
          min_withdrawable: 0,
          wait_time: 1
        }
      },
      qrCodeDialog: {
        show: false,
        data: null
      }
    }
  },
  computed: {
    sortedWithdrawLinks: function () {
      return this.withdrawLinks.sort(function (a, b) {
        return b.uses_left - a.uses_left
      })
    }
  },
  methods: {
    getWithdrawLinks: function () {
      var self = this

      LNbits.api
        .request(
          'GET',
          '/offlinelnurlw/api/v1/links?all_wallets',
          this.g.user.wallets[0].inkey
        )
        .then(function (response) {
          self.withdrawLinks = response.data.map(function (obj) {
            return mapWithdrawLink(obj)
          })
        })
        .catch(function (error) {
          clearInterval(self.checker)
          LNbits.utils.notifyApiError(error)
        })
    },
    closeFormDialog: function () {
      this.formDialog.data = {
        is_unique: false
      }
    },
    simplecloseFormDialog: function () {
      this.simpleformDialog.data = {
        is_unique: false
      }
    },
    openQrCodeDialog: function (linkId) {
      var link = _.findWhere(this.withdrawLinks, {id: linkId})

      this.qrCodeDialog.data = _.clone(link)
      console.log(this.qrCodeDialog.data)
      this.qrCodeDialog.data.url = window.location.host
      this.qrCodeDialog.show = true
    },
    openUpdateDialog: function (linkId) {
      var link = _.findWhere(this.withdrawLinks, {id: linkId})
      this.formDialog.data = _.clone(link._data)
      this.formDialog.show = true
    },
    sendFormData: function () {
      var wallet = _.findWhere(this.g.user.wallets, {
        id: this.formDialog.data.wallet
      })
      var data = _.omit(this.formDialog.data, 'wallet')

      if (data.id) {
        this.updateWithdrawLink(wallet, data)
      } else {
        this.createWithdrawLink(wallet, data)
      }
    },
    simplesendFormData: function () {
      var wallet = _.findWhere(this.g.user.wallets, {
        id: this.simpleformDialog.data.wallet
      })
      var data = _.omit(this.simpleformDialog.data, 'wallet')

      if (data.id) {
        this.updateWithdrawLink(wallet, data)
      } else {
        this.createWithdrawLink(wallet, data)
      }
    },
    updateWithdrawLink: function (wallet, data) {
      var self = this

      LNbits.api
        .request(
          'PUT',
          '/offlinelnurlw/api/v1/links/' + data.id,
          wallet.adminkey,
          _.pick(
            data,
            'title'
          )
        )
        .then(function (response) {
          self.withdrawLinks = _.reject(self.withdrawLinks, function (obj) {
            return obj.id === data.id
          })
          self.withdrawLinks.push(mapWithdrawLink(response.data))
          self.formDialog.show = false
        })
        .catch(function (error) {
          LNbits.utils.notifyApiError(error)
        })
    },
    createWithdrawLink: function (wallet, data) {
      var self = this

      LNbits.api
        .request('POST', '/offlinelnurlw/api/v1/links', wallet.adminkey, data)
        .then(function (response) {
          self.withdrawLinks.push(mapWithdrawLink(response.data))
          self.formDialog.show = false
          self.simpleformDialog.show = false
        })
        .catch(function (error) {
          LNbits.utils.notifyApiError(error)
        })
    },
    deleteWithdrawLink: function (linkId) {
      var self = this
      var link = _.findWhere(this.withdrawLinks, {id: linkId})

      LNbits.utils
        .confirmDialog('Are you sure you want to delete this offline withdraw link?')
        .onOk(function () {
          LNbits.api
            .request(
              'DELETE',
              '/offlinelnurlw/api/v1/links/' + linkId,
              _.findWhere(self.g.user.wallets, {id: link.wallet}).adminkey
            )
            .then(function (response) {
              self.withdrawLinks = _.reject(self.withdrawLinks, function (obj) {
                return obj.id === linkId
              })
            })
            .catch(function (error) {
              LNbits.utils.notifyApiError(error)
            })
        })
    },
    exportCSV: function () {
      LNbits.utils.exportCSV(this.paywallsTable.columns, this.paywalls)
    }
  },
  created: function () {
    var self = this
    self.format = window.location.hostname
    if (self.g.user.wallets.length) {
      var getWithdrawLinks = self.getWithdrawLinks
      getWithdrawLinks()
      self.checker = setInterval(function () {
        getWithdrawLinks()
      }, 20000)
    }
  }
})
