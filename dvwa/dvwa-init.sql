CREATE TABLE users (
  user_id INT(6),
  first_name VARCHAR(15),
  last_name VARCHAR(15),
  user VARCHAR(15),
  password VARCHAR(32),
  avatar VARCHAR(70),
  last_login TIMESTAMP,
  failed_login INT(3),
  role VARCHAR(20) DEFAULT 'user',
  account_enabled TINYINT(1) DEFAULT 1,
  PRIMARY KEY (user_id)
);

INSERT INTO users VALUES
  ('1', 'admin', 'admin', 'admin', MD5('password'), '/hackable/users/admin.jpg', NOW(), '0', 'admin', 1),
  ('2', 'Gordon', 'Brown', 'gordonb', MD5('abc123'), '/hackable/users/gordonb.jpg', NOW(), '0', 'user', 1),
  ('3', 'Hack', 'Me', '1337', MD5('charley'), '/hackable/users/1337.jpg', NOW(), '0', 'user', 1),
  ('4', 'Pablo', 'Picasso', 'pablo', MD5('letmein'), '/hackable/users/pablo.jpg', NOW(), '0', 'user', 1),
  ('5', 'Bob', 'Smith', 'smithy', MD5('password'), '/hackable/users/smithy.jpg', NOW(), '0', 'user', 1);

CREATE TABLE access_log (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  target_id INT NOT NULL,
  action VARCHAR(50) NOT NULL,
  timestamp DATETIME NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(user_id),
  FOREIGN KEY (target_id) REFERENCES users(user_id)
) ENGINE=InnoDB;

CREATE TABLE security_log (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  target_id INT NOT NULL,
  action VARCHAR(50) NOT NULL,
  timestamp DATETIME NOT NULL,
  ip_address VARCHAR(45) NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(user_id),
  FOREIGN KEY (target_id) REFERENCES users(user_id)
) ENGINE=InnoDB;

CREATE TABLE guestbook (
  comment_id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
  comment VARCHAR(300),
  name VARCHAR(100),
  PRIMARY KEY (comment_id)
);

INSERT INTO guestbook VALUES ('1', 'This is a test comment.', 'test');
