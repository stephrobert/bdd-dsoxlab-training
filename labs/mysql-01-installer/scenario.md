# A database put on the network without anyone meaning to

`db1.lab` is a fresh Debian 13 machine. You are asked to put MySQL 8.4 LTS on
it, the long-term support release, from Oracle's repository and not from
Debian's, which ships MariaDB under similar names.

So far, nothing remarkable. What is more remarkable is what the installation
leaves behind.

Oracle's packages lay down **no** `bind-address` line, not even a commented
one. Yet that variable defaults to `*`, meaning every interface. At the end of
an `apt install`, `mysqld` therefore listens on the network, on **two** ports:
3306 for the classic protocol, 33060 for the X protocol.

And there is a second level to the trap. `bind-address` does **not** restrict
port 33060: the X protocol has its own variable. So you can set
`bind-address = 127.0.0.1`, see `SELECT @@bind_address` answer `127.0.0.1`, and
leave 33060 wide open.

You are therefore asked to establish the real state rather than assume it, and
to close both doors. A `root@localhost` account protects the **accounts**, not
the **network**.

The `root` password to set is `R00t!Lab2026`.

The guide: [https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/installation/](https://www.stephane-robert.info/docs/services/bdd/relationnelles/mysql/installation/)
