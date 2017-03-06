import tensorflow as tf
import os


W = tf.Variable(tf.zeros([5, 1]), name='weights')
b = tf.Variable(0., name='bias')


# former inference is now used for combining inputs
def combine_inputs(X):
    return tf.matmul(X, W) + b


# define the training loop operations
def inference(X):
    # computer inference model over data X and return the result
    return tf.sigmoid(combine_inputs(X))
    

def loss(X, Y):
    # computer loss over training data X and expected outputs Y
    return tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(combine_inputs(X), Y))


def read_csv(batch_size, filename, record_defaults):
    # https://www.tensorflow.org/how_tos/reading_data/
    filename_queue = tf.train.string_input_producer([os.path.join(os.getcwd(), filename)])
    
    reader = tf.TextLineReader(skip_header_lines=1)
    key, value = reader.read(filename_queue)
    
    # decode_csv will convert a Tensor from type string (the text line) in
    # a tuple of tensor columns with the specified defaults, which also,
    # sets the data type for each column
    decoded = tf.decode_csv(value, record_defaults=record_defaults)
    
    # batch actually reads the file and loads "batch_size" rows in a single tensor
    return tf.train.shuffle_batch(decoded, batch_size=batch_size,
                                  capacity=batch_size * 50, min_after_dequeue=batch_size)


def inputs():
    # read/generate input training data X and expected outputs Y
    # https://www.kaggle.com/c/titanic/data
    passenger_id, survived, pclass, name, sex, age, sibsp, parch, ticket, fare, cabin, embarked = \
        read_csv(100, 'train.csv', [[0.0], [0.0], [0], [""], [""], [0.0], [0.0], [0.0], [""], [0.0], [""], [""]])
        
    # convert categorical data
    is_first_class = tf.to_float(tf.equal(pclass, [1]))
    is_second_class = tf.to_float(tf.equal(pclass, [2]))
    is_third_class = tf.to_float(tf.equal(pclass, [3]))
    
    gender = tf.to_float(tf.equal(sex, ["female"]))
    
    # finally we pack all the features in a single matrix;
    # we then transpose to have a matrix with one example per row and one feature per column.
    features = tf.transpose(tf.pack([is_first_class, is_second_class, is_third_class, gender, age]))
    survived = tf.reshape(survived, [100, 1])
    
    return features, survived


def train(total_loss):
    # train / adjust model parameters according to computed total loss
    learning_rate = 0.01
    return tf.train.GradientDescentOptimizer(learning_rate).minimize(total_loss)


def evaluate(sess, X, Y):
    # evaluate the resulting trained model
    predicted = tf.cast(inference(X) > 0.5, tf.float32)
    print sess.run(tf.reduce_mean(tf.cast(tf.equal(predicted, Y), tf.float32)))


saver = tf.train.Saver()

# launch the graph in a session, setup boilerplate
with tf.Session() as sess:
    tf.initialize_all_variables().run()
    
    X, Y = inputs()
    
    total_loss = loss(X, Y)
    train_op = train(total_loss)
    
    coord = tf.train.Coordinator()
    threads = tf.train.start_queue_runners(sess=sess, coord=coord)
    
    initial_step = 0 
    
    # verify if we don't have a checkpoint saved already
    #ckpt = tf.train.get_checkpoint_state(os.path.dirname("."))
    #if ckpt and ckpt.model_checkpoint_path:
    #    #Restores from checkpoint
    #    saver.restore(sess, ckpt.model_checkpoint_path)
    #    initial_step = int(ckpt.model_checkpoint_path.rsplit('-', 1)[1])
        
    training_steps = 1000
    for step in range(initial_step, training_steps):
        sess.run([train_op])
        
        #if step % 1000 == 0:
        #    saver.save(sess, 'my-model', global_step=step)
            
        # for debugging and learning purposes, see how the loss gets decremented through training steps.
        if step % 10 == 0:
            print "loss: ", sess.run([total_loss])
                
    evaluate(sess, X, Y)
    
    #saver.save(sess, 'my-model', global_step=training_steps)
    
    coord.request_stop()
    coord.join(threads)
    sess.close()
