import nodemailer from 'nodemailer';

export const sendEmail = async (recipientMail, otp) => {
  const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: {
      user: process.env.senderEmail,
      pass: process.env.senderPwd,
    },
  });

  const mailOptions = {
    from: process.env.senderEmail, 
    to: recipientMail, 
    subject: 'OTP for reset password - Divyansh Jindal', 
    text: `Your OTP for the reset of password is ${otp}`,
  };
    
  try {
    const info = await transporter.sendMail(mailOptions);
    console.log('Email sent: ' + info.response);
  } catch (error) {
    console.error('Error sending email:', error);
  }
};