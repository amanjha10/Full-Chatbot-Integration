import React, { useState, useEffect, useRef } from 'react';
import { 
  FaFacebook, 
  FaInstagram, 
  FaTiktok, 
  FaYoutube, 
  FaArrowRight, 
  FaPhone,
  FaBars,
  FaTimes,
  FaCheck
} from 'react-icons/fa';

interface CounterProps {
  target: number;
  label: string;
  suffix?: string;
}

const Counter: React.FC<CounterProps> = ({ target, label, suffix = '+' }) => {
  const [count, setCount] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const counterRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !isVisible) {
          setIsVisible(true);
          animateCounter();
        }
      },
      { threshold: 0.3 }
    );

    if (counterRef.current) {
      observer.observe(counterRef.current);
    }

    return () => observer.disconnect();
  }, [isVisible]);

  const animateCounter = () => {
    const duration = 2000;
    const steps = 60;
    const increment = target / steps;
    let current = 0;
    let step = 0;

    const updateCounter = () => {
      if (step < steps) {
        current += increment;
        step++;
        const progress = step / steps;
        const easeOutCubic = 1 - Math.pow(1 - progress, 3);
        const displayValue = Math.floor(target * easeOutCubic);
        setCount(displayValue);
        requestAnimationFrame(updateCounter);
      } else {
        setCount(target);
      }
    };

    updateCounter();
  };

  return (
    <div ref={counterRef} className="text-center p-6 bg-white rounded-lg border border-gray-200 transition-all duration-300 hover:-translate-y-1 hover:shadow-lg">
      <div className="text-4xl md:text-3xl font-bold text-orange-500 mb-2">
        {count}{label.includes('%') ? '%' : suffix}
      </div>
      <div className="text-sm font-semibold text-gray-700">{label}</div>
    </div>
  );
};

const ExcellenceConsultancy: React.FC = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      if (window.innerWidth > 768) {
        setIsScrolled(window.scrollY > 50);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      const offsetTop = window.innerWidth <= 768 ? element.offsetTop : element.offsetTop - 80;
      window.scrollTo({ top: offsetTop, behavior: 'smooth' });
    }
    setIsMenuOpen(false);
  };

  const navLinks = [
    { id: 'home', label: 'Home' },
    { id: 'services', label: 'Services' },
    { id: 'about', label: 'About' },
    { id: 'why-us', label: 'Why Us' },
    { id: 'testimonials', label: 'Reviews' },
  ];

  const services = [
    {
      title: 'Educational Consultancies',
      description: 'Engage prospects and manage inquiries smoothly.',
      features: ['Instant FAQs', 'Course guidance', 'Appointment scheduling', 'Document submission help']
    },
    {
      title: 'Schools',
      description: 'Improve student and parent engagement with our assistance.',
      features: ['Student inquiries', 'Parent inquiries', 'Academic support', 'Event notifications']
    },
    {
      title: 'Banks',
      description: 'Provide quick and secure customer support.',
      features: ['Account inquiries', 'Loan information', '24/7 customer support', 'Transaction assistance']
    },
    {
      title: 'Hospitals',
      description: 'Enhance patient care with instant chatbot services.',
      features: ['Appointment booking', 'Patient follow-ups', 'Emergency contacts', 'Medical inquiries']
    },
    {
      title: 'Ecommerce',
      description: 'Support your customers and boost your sales.',
      features: ['Order tracking', 'Product recommendations', 'Returns and refunds', 'Payment assistance']
    },
    {
      title: 'Hotels',
      description: 'Deliver smooth guest services and booking help via chatbots.',
      features: ['Booking management', 'Room service requests', 'Local information', 'Guest assistance']
    }
  ];

  const testimonials = [
    {
      content: "Excellence Consultancy helped us navigate the complex regulatory landscape and expand our operations across three major cities in Nepal. Their strategic guidance was invaluable.",
      author: "Rajesh Shrestha",
      role: "CEO, Himalayan Enterprises",
      avatar: "RS"
    },
    {
      content: "The digital transformation strategy they developed increased our operational efficiency by 40% and significantly improved our customer satisfaction scores.",
      author: "Sita Poudel",
      role: "Director, Tech Solutions Nepal",
      avatar: "SP"
    },
    {
      content: "Their financial advisory services helped us secure funding and implement sustainable growth strategies that doubled our revenue in two years.",
      author: "Arjun KC",
      role: "Founder, Green Valley Industries",
      avatar: "AK"
    }
  ];

  const whyChooseUs = [
    {
      title: 'Cutting-Edge Technology',
      features: ['Smart AI conversations', 'Regular updates']
    },
    {
      title: 'Customizable Solutions',
      features: ['Suitable for any business', 'Simple integration']
    },
    {
      title: 'Customer Engagement',
      features: ['Instant 24/7 replies', 'Personalized support']
    },
    {
      title: 'Cost and Time Efficiency',
      features: ['Automates tasks', 'Less support costs']
    },
    {
      title: 'Support and Maintenance',
      features: ['Continuous assistance', 'Performance report']
    },
    {
      title: 'Scalable and Flexible',
      features: ['Grows with you', 'Readily adjustable']
    }
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className={`fixed top-0 w-full z-50 transition-all duration-300 ${
        isScrolled ? 'bg-white/95 backdrop-blur-lg py-2 shadow-md' : 'bg-white/95 backdrop-blur-lg py-4'
      } md:${isScrolled ? 'py-2' : 'py-4'} border-b border-gray-100`}>
        <div className="max-w-6xl mx-auto px-8 flex justify-between items-center">
          <div className="text-2xl font-bold text-purple-800">
            Excellence Consultancy
          </div>
          
          {/* Desktop Menu */}
          <div className="hidden md:flex items-center space-x-8">
            {navLinks.map(link => (
              <button
                key={link.id}
                onClick={() => scrollToSection(link.id)}
                className="text-gray-700 hover:text-purple-800 font-medium transition-colors px-4 py-2 rounded-lg hover:bg-purple-100"
              >
                {link.label}
              </button>
            ))}
            <button
              onClick={() => scrollToSection('contact')}
              className="bg-orange-500 text-white px-6 py-2 rounded-lg font-semibold hover:bg-orange-600 transition-all hover:-translate-y-0.5"
            >
              Get Started
            </button>
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden p-2"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            {isMenuOpen ? <FaTimes size={24} /> : <FaBars size={24} />}
          </button>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <div className="md:hidden bg-white/95 backdrop-blur-lg border-t border-gray-100 py-4">
            <div className="flex flex-col space-y-4 px-8">
              {navLinks.map(link => (
                <button
                  key={link.id}
                  onClick={() => scrollToSection(link.id)}
                  className="text-left text-gray-700 hover:text-purple-800 font-medium py-2"
                >
                  {link.label}
                </button>
              ))}
              <button
                onClick={() => scrollToSection('contact')}
                className="bg-orange-500 text-white px-6 py-2 rounded-lg font-semibold text-center mt-4"
              >
                Get Started
              </button>
            </div>
          </div>
        )}
      </nav>

      {/* Hero Section */}
      <section id="home" className="min-h-screen bg-purple-800 text-white pt-20 md:pt-24 relative overflow-hidden">
        <div className="absolute inset-0 opacity-20">
          <div className="absolute top-20 left-20 w-20 h-20 bg-white rounded-full opacity-10 animate-pulse"></div>
          <div className="absolute top-40 right-20 w-24 h-24 bg-white rounded-full opacity-10 animate-pulse delay-1000"></div>
          <div className="absolute bottom-40 left-1/3 w-28 h-28 bg-white rounded-full opacity-10 animate-pulse delay-2000"></div>
        </div>
        
        <div className="max-w-6xl mx-auto px-8 grid md:grid-cols-2 gap-12 items-center min-h-[80vh]">
          <div className="space-y-8 text-center md:text-left">
            <div className="inline-block bg-white/20 backdrop-blur-lg px-4 py-2 rounded-lg border border-white/30">
              Your Success Partner in Nepal
            </div>
            <h1 className="text-4xl md:text-6xl font-bold leading-tight">
              Innovation for a Smarter Future
            </h1>
            <p className="text-xl opacity-90 leading-relaxed">
              Committed to delivering intelligent, reliable, and user-friendly chatbot solutions that combine technology, innovation, and customer satisfaction to transform the way you connect with your audience.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center md:justify-start">
              <button
                onClick={() => scrollToSection('services')}
                className="bg-orange-500 text-white px-8 py-4 rounded-lg font-semibold flex items-center justify-center gap-2 hover:bg-orange-600 transition-all hover:-translate-y-1 shadow-lg"
              >
                Explore Services <FaArrowRight />
              </button>
              <button
                onClick={() => scrollToSection('contact')}
                className="bg-white/20 border-2 border-white/30 backdrop-blur-lg text-white px-8 py-4 rounded-lg font-semibold flex items-center justify-center gap-2 hover:bg-white/30 transition-all hover:-translate-y-1"
              >
                <FaPhone /> Free Consultation
              </button>
            </div>
          </div>
          
          <div className="flex justify-center">
            <div className="w-full max-w-lg aspect-square bg-gradient-to-br from-purple-600 to-purple-900 rounded-3xl p-8 shadow-2xl">
              <div className="grid grid-cols-2 gap-6 mb-8">
                <div className="text-center">
                  <div className="text-3xl font-bold text-orange-500">47+</div>
                  <div className="text-sm opacity-80">Projects</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-orange-500">157+</div>
                  <div className="text-sm opacity-80">Clients</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-orange-500">5+</div>
                  <div className="text-sm opacity-80">Years</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-orange-500">99%</div>
                  <div className="text-sm opacity-80">Success</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Services Section */}
      <section id="services" className="py-20 bg-gray-100">
        <div className="max-w-6xl mx-auto px-8">
          <div className="text-center mb-16">
            <div className="text-2xl font-semibold mb-4">Our Expertise</div>
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
              Comprehensive Business Solutions
            </h2>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {services.map((service, index) => (
              <div key={index} className="bg-white rounded-lg p-8 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-2 border-t-4 border-transparent hover:border-purple-800">
                <h3 className="text-xl font-bold text-gray-900 mb-4">{service.title}</h3>
                <p className="text-gray-600 mb-6">{service.description}</p>
                <ul className="space-y-2">
                  {service.features.map((feature, i) => (
                    <li key={i} className="flex items-center gap-2 text-sm text-gray-600">
                      <FaCheck className="text-green-500 text-xs" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* About Section */}
      <section id="about" className="py-20 bg-white">
        <div className="max-w-6xl mx-auto px-8">
          <div className="grid md:grid-cols-2 gap-16 items-center">
            <div className="space-y-8">
              <h2 className="text-4xl md:text-5xl font-bold text-gray-900 leading-tight">
                Your Reliable Partners in Digital Growth
              </h2>
              <div className="space-y-6 text-lg text-gray-600">
                <p>
                  With over 5 years of experience serving businesses across Nepal, we have established ourselves as the premier consultancy partner for organizations seeking sustainable growth and competitive advantage.
                </p>
                <p>
                  Our expert team uses creative strategies and innovative chatbot technologies that improve your company's performance. Our primary objectives are to increase consumer engagement, automate processes, and provide tailored digital experiences that enhance your company's success.
                </p>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                {['Award-Winning Team', 'Client-Centric Approach', 'Innovative Solutions', 'Proven Results'].map((feature, index) => (
                  <div key={index} className="flex items-center gap-3 p-4 bg-gray-50 rounded-xl">
                    <div className="w-8 h-8 bg-purple-800 rounded-lg flex items-center justify-center text-white text-sm font-bold">
                      {index + 1}
                    </div>
                    <span className="font-semibold text-gray-900 text-sm">{feature}</span>
                  </div>
                ))}
              </div>
              
              <button
                onClick={() => scrollToSection('contact')}
                className="bg-orange-500 text-white px-8 py-4 rounded-lg font-semibold hover:bg-orange-600 transition-all hover:-translate-y-1"
              >
                Learn More About Us
              </button>
            </div>
            
            <div className="flex justify-center">
              <div className="w-full max-w-md aspect-square bg-gradient-to-br from-purple-800 to-purple-900 rounded-3xl flex items-center justify-center shadow-2xl">
                <div className="text-center text-white p-8">
                  <h3 className="text-2xl font-bold mb-4">Excellence in Action</h3>
                  <p className="opacity-90 mb-8">Transforming businesses across Nepal with innovative solutions</p>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white/20 backdrop-blur-lg rounded-xl p-4 border border-white/20">
                      <div className="text-2xl font-bold text-orange-500">47+</div>
                      <div className="text-xs opacity-80">Projects</div>
                    </div>
                    <div className="bg-white/20 backdrop-blur-lg rounded-xl p-4 border border-white/20">
                      <div className="text-2xl font-bold text-orange-500">5+</div>
                      <div className="text-xs opacity-80">Years</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Why Choose Us */}
      <section id="why-us" className="py-20 bg-gray-100">
        <div className="max-w-6xl mx-auto px-8">
          <div className="text-center mb-16">
            <div className="text-2xl font-semibold mb-4">Our Advantages</div>
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900">Why Us?</h2>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {whyChooseUs.map((item, index) => (
              <div key={index} className="bg-white rounded-lg p-8 text-center shadow-md hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
                <h3 className="text-xl font-bold text-purple-800 mb-4">{item.title}</h3>
                <ul className="space-y-3">
                  {item.features.map((feature, i) => (
                    <li key={i} className="text-gray-600 text-sm flex items-start gap-2">
                      <span className="text-orange-500 font-bold">*</span>
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section id="testimonials" className="py-20 bg-white">
        <div className="max-w-6xl mx-auto px-8">
          <div className="text-center mb-16">
            <div className="text-2xl font-semibold mb-4">Client Success Stories</div>
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900">What Our Clients Say</h2>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <div key={index} className="bg-white border border-gray-200 rounded-lg p-8 shadow-md hover:shadow-lg transition-shadow">
                <div className="flex flex-col h-full justify-between">
                  <p className="text-gray-600 italic mb-6 leading-relaxed">"{testimonial.content}"</p>
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-orange-500 rounded-full flex items-center justify-center text-white font-bold">
                      {testimonial.avatar}
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900">{testimonial.author}</h4>
                      <span className="text-sm text-gray-500">{testimonial.role}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Excellence Numbers */}
      <section className="py-20 bg-gray-100">
        <div className="max-w-6xl mx-auto px-8 text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-12">Excellence in Numbers</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <Counter target={47} label="Projects Completed" />
            <Counter target={157} label="Happy Clients" />
            <Counter target={5} label="Years Experience" />
            <Counter target={99} label="Success Rate %" suffix="%" />
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section id="contact" className="py-20 bg-white text-center">
        <div className="max-w-4xl mx-auto px-8">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            Ready to Transform Your Business?
          </h2>
          <button className="bg-orange-500 text-white px-12 py-4 rounded-lg font-semibold text-lg hover:bg-orange-600 transition-all hover:-translate-y-1 shadow-lg">
            Schedule Free Consultation
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-purple-800 text-white py-16">
        <div className="max-w-6xl mx-auto px-8">
          <div className="grid md:grid-cols-4 gap-12 mb-8">
            <div className="space-y-4">
              <h3 className="text-xl font-bold text-orange-500">Excellence Consultancy</h3>
              <p className="opacity-80 leading-relaxed">
                Nepal's premier business consultancy firm, dedicated to driving sustainable growth and innovation across industries.
              </p>
              <div className="flex gap-4">
                {[
                  { icon: FaFacebook, href: "https://www.facebook.com/spellinnovation" },
                  { icon: FaInstagram, href: "https://www.instagram.com/spellinnovation" },
                  { icon: FaTiktok, href: "https://www.tiktok.com/@spellinnovation" },
                  { icon: FaYoutube, href: "https://www.youtube.com/@spellinnovation" }
                ].map((social, index) => (
                  <a
                    key={index}
                    href={social.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center hover:bg-orange-500 transition-colors"
                  >
                    <social.icon size={20} />
                  </a>
                ))}
              </div>
            </div>
            
            <div>
              <h3 className="text-xl font-bold text-orange-500 mb-4">Our Services</h3>
              <ul className="space-y-2 opacity-80">
                {services.map((service, index) => (
                  <li key={index}>{service.title}</li>
                ))}
              </ul>
            </div>
            
            <div>
              <h3 className="text-xl font-bold text-orange-500 mb-4">Company</h3>
              <ul className="space-y-2 opacity-80">
                <li>About Us</li>
                <li>Our Team</li>
                <li>Case Studies</li>
                <li>Careers</li>
                <li>Contact</li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-xl font-bold text-orange-500 mb-4">Contact Information</h3>
              <div className="space-y-2 opacity-80 text-sm">
                <p>Email: contact@spellinnovation.com</p>
                <p>Phone: 01-5910781</p>
                <p>Mobile: +977-9801047737</p>
                <p>Address: Pipal bot, Mid baneswor, Kathmandu, Nepal</p>
                <p>Time: Mon-Fri: 9:00 AM - 6:00 PM</p>
              </div>
            </div>
          </div>
          
          <div className="text-center pt-8 border-t border-white/20 opacity-60">
            <p>&copy; 2025 Excellence Consultancy Nepal. All rights reserved.</p>
          </div>
        </div>
      </footer>

      {/* Chatbot Icon */}
      <div className="fixed bottom-20 right-8 z-50">
        <button
          onClick={() => window.location.href = '/chatbot'}
          className="w-16 h-16 bg-white rounded-full shadow-2xl flex items-center justify-center hover:scale-110 transition-transform animate-bounce"
          title="Chat with our Study Abroad Assistant"
        >
          <div className="w-12 h-12 bg-purple-800 rounded-full flex items-center justify-center text-white font-bold">
            AI
          </div>
        </button>
      </div>
    </div>
  );
};

export default ExcellenceConsultancy;